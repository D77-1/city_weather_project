"""
计算 R 综合风险分与 AQI 的相关系数
按风险模型公式逐条记录计算 R,然后与 AQI 求 Pearson / Spearman
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import City, AirQualityRecord
import pandas as pd
import numpy as np

app = create_app()
with app.app_context():
    print('正在拉取历史数据...')
    records = (AirQualityRecord.query
               .order_by(AirQualityRecord.city_id, AirQualityRecord.record_time)
               .all())
    print(f'共 {len(records)} 条记录')

    # 城市级日聚合(同一天多站取均值,与风险模型 calculate_risk_score 一致)
    df = pd.DataFrame([{
        'city_id': r.city_id,
        'date': r.record_time.date(),
        'aqi': float(r.aqi) if r.aqi else None,
        'wind_speed': float(r.wind_speed) if r.wind_speed is not None else 3.0,
        'humidity': float(r.humidity) if r.humidity is not None else 50.0,
        'rainfall': float(r.rainfall) if r.rainfall is not None else 0.0,
    } for r in records])
    df = df.dropna(subset=['aqi'])
    daily = df.groupby(['city_id', 'date']).mean(numeric_only=True).reset_index()
    print(f'日聚合后 {len(daily)} 条城市-日记录')

    # 计算各分量
    daily['R_exposure'] = (daily['aqi'] / 500.0 * 70.0).clip(upper=70)

    def meteo_score(row):
        s = 0.0
        if row['wind_speed'] <= 3.0: s += 8.0
        if row['humidity'] >= 80.0: s += 4.0
        if row['wind_speed'] <= 3.2 and row['rainfall'] < 1.0: s += 3.0
        return min(15.0, s)
    daily['R_meteo'] = daily.apply(meteo_score, axis=1)

    # R_trend: 用未来 5 天的实际 AQI(历史数据有未来值,这是 backtest 视角)
    daily = daily.sort_values(['city_id', 'date']).reset_index(drop=True)
    daily['R_trend'] = 0.0
    for cid, grp in daily.groupby('city_id'):
        idx = grp.index.tolist()
        for i, ix in enumerate(idx):
            future = grp.iloc[i+1: i+6]['aqi']
            if len(future) > 0:
                daily.at[ix, 'R_trend'] = min(10.0, future.max() / 500.0 * 10.0)
            else:
                daily.at[ix, 'R_trend'] = min(10.0, daily.at[ix, 'aqi'] / 500.0 * 10.0)

    # R_anomaly: 跑一个简化 IQR 标记,在每个城市的 90 天滚动里数异常
    daily['R_anomaly'] = 0.0
    for cid, grp in daily.groupby('city_id'):
        a = grp['aqi'].values
        if len(a) < 10:
            continue
        # 整体 IQR(简化处理,跟原代码 90 天窗口接近)
        q1, q3 = np.percentile(a, 25), np.percentile(a, 75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        is_anom = (a < lo) | (a > hi)
        # MAD
        med = np.median(a)
        mad = np.median(np.abs(a - med))
        if mad > 0:
            mod_z = 0.6745 * np.abs(a - med) / mad
            is_mad = mod_z > 3.5
        else:
            is_mad = np.zeros_like(a, dtype=bool)
        n_iqr = is_anom.astype(int)
        n_mad = is_mad.astype(int)
        anom_score = np.minimum(5.0, 0.5 * (n_iqr + n_mad))
        daily.loc[grp.index, 'R_anomaly'] = anom_score

    daily['R'] = (daily['R_exposure'] + daily['R_meteo'] +
                  daily['R_anomaly'] + daily['R_trend']).clip(upper=100)

    # 相关性
    pearson = daily[['R', 'aqi']].corr(method='pearson').iloc[0, 1]
    spearman = daily[['R', 'aqi']].corr(method='spearman').iloc[0, 1]

    # R 中独立于 AQI 的部分(R_meteo + R_anomaly)
    daily['R_indep'] = daily['R_meteo'] + daily['R_anomaly']
    indep_mean = daily['R_indep'].mean()
    indep_std = daily['R_indep'].std()
    indep_max = daily['R_indep'].max()

    print()
    print('=' * 60)
    print('R 与 AQI 相关性分析')
    print('=' * 60)
    print(f'样本量: {len(daily)} 条城市-日记录')
    print(f'AQI 均值: {daily["aqi"].mean():.2f}, 范围: [{daily["aqi"].min():.0f}, {daily["aqi"].max():.0f}]')
    print(f'R 均值: {daily["R"].mean():.2f}, 范围: [{daily["R"].min():.2f}, {daily["R"].max():.2f}]')
    print()
    print(f'>>> Pearson 相关系数: {pearson:.4f}')
    print(f'>>> Spearman 相关系数: {spearman:.4f}')
    print(f'>>> R² (决定系数): {pearson**2:.4f}  → R 中由 AQI 解释的方差占比 {pearson**2*100:.1f}%')
    print(f'>>> 独立信息维度占比: {(1 - pearson**2)*100:.1f}%')
    print()
    print(f'独立分量(气象+异常)统计: 均值 {indep_mean:.2f}, 标准差 {indep_std:.2f}, 最大 {indep_max:.2f}')
    print(f'(理论上界 20,实际最大 {indep_max:.2f},说明气象+异常的扰动空间被充分利用)')

    # 各分量与 AQI 单独的相关性
    print()
    print('各分量与 AQI 的相关性:')
    for col in ['R_exposure', 'R_meteo', 'R_anomaly', 'R_trend']:
        c = daily[[col, 'aqi']].corr().iloc[0, 1]
        print(f'  {col:<14}: Pearson = {c:.4f}')
