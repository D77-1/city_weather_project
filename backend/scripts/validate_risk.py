"""
风险评分一致性验证脚本
--------------------------------
在数据库全部历史记录上，按 §4.3.3 综合风险评分公式计算一份**简化版** R 评分
（exposure + meteo + 简化版 anomaly + 简化版 trend），并把 R 的 4 级划分
（low/medium/high/severe）与该天 AQI 按 HJ 633-2012 六级分类（合并为 4 级）做
交叉对比，输出一致率、混淆矩阵、权重/阈值敏感性以及 train/test split 验证。

用法：
    D:/conda_envs/python3.12/python.exe backend/scripts/validate_risk.py

⚠ 重要：本脚本并非在线评分模块的精确复刻，为在 14 万+ 条记录上批量验证可行，
对两个分项做了简化处理，**论文 6.3.1 实验设计应与此处口径完全一致**：
 - 异常分（简化）：当条记录的 AQI 是否落在本城市全期 IQR ± 1.5 倍范围之外；
   命中即给满分 R_ano（5 分），否则 0 分。在线模块按"近 60 天 IQR + MAD
   命中数 × 0.5"计算。
 - 趋势分（简化）：当条记录与本城市前 5 日滚动均值的差值占 500 的比例，
   按 R_trend 上限截断。在线模块按"未来 5 天 Holt-Winters 预测峰值 / 500 ×
   R_trend"计算（即基于前向预测，本脚本因批量回测改用历史滚动均值代替）。

这两项简化只影响 R_anomaly 与 R_trend 这两个小分项（合计 15 / 100），
不改变 R_exposure（70 / 100）与 HJ 633-2012 标签均为 AQI 单调函数这一结构事实，
因此一致率分析的方向性结论可以迁移到在线模块。
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from app import create_app, db
from app.models import AirQualityRecord


def aqi_to_hj633_level(aqi):
    """HJ 633-2012 六级分类 → 合并为 4 级"""
    if aqi <= 100:
        return 'low'      # 优 / 良
    if aqi <= 150:
        return 'medium'   # 轻度污染
    if aqi <= 300:
        return 'high'     # 中度 / 重度污染
    return 'severe'       # 严重污染


def r_to_level(r, t_med=20, t_high=35, t_severe=55):
    if r >= t_severe:
        return 'severe'
    if r >= t_high:
        return 'high'
    if r >= t_med:
        return 'medium'
    return 'low'


def compute_r(row, w_exp=70, w_meteo=15, w_ano=5, w_trend=10,
              aqi_bg_q1=None, aqi_bg_q3=None, rolling_mean=None):
    aqi = row['aqi'] or 0
    wind = row['wind_speed'] or 0
    hum = row['humidity'] or 0
    rain = row['rainfall'] or 0

    # 暴露
    exposure = min(w_exp, aqi / 500.0 * w_exp)

    # 气象 (QX/T 113-2010 + Horton 2014)
    meteo_parts = 0.0
    if wind <= 3.0:
        meteo_parts += w_meteo * 8 / 15
    if hum >= 80.0:
        meteo_parts += w_meteo * 4 / 15
    if wind <= 3.2 and rain < 1.0:
        meteo_parts += w_meteo * 3 / 15
    meteo = min(w_meteo, meteo_parts)

    # 异常：该天是否落在同城市历史 IQR 之外
    anomaly = 0.0
    if aqi_bg_q1 is not None and aqi_bg_q3 is not None:
        iqr = aqi_bg_q3 - aqi_bg_q1
        if aqi > aqi_bg_q3 + 1.5 * iqr or aqi < aqi_bg_q1 - 1.5 * iqr:
            anomaly = w_ano

    # 趋势：相比前期滚动均值的上升幅度
    trend = 0.0
    if rolling_mean is not None and rolling_mean > 0:
        growth_ratio = max(0.0, (aqi - rolling_mean) / 500.0)
        trend = min(w_trend, growth_ratio * w_trend * 2)

    return min(100.0, exposure + meteo + anomaly + trend)


def load_records():
    q = db.session.query(
        AirQualityRecord.city_id,
        AirQualityRecord.record_time,
        AirQualityRecord.aqi,
        AirQualityRecord.wind_speed,
        AirQualityRecord.humidity,
        AirQualityRecord.rainfall,
    ).filter(AirQualityRecord.aqi.isnot(None)).all()
    df = pd.DataFrame([{
        'city_id': r.city_id,
        'date': r.record_time,
        'aqi': float(r.aqi) if r.aqi is not None else None,
        'wind_speed': float(r.wind_speed) if r.wind_speed is not None else 0.0,
        'humidity': float(r.humidity) if r.humidity is not None else 0.0,
        'rainfall': float(r.rainfall) if r.rainfall is not None else 0.0,
    } for r in q])
    df = df.sort_values(['city_id', 'date']).reset_index(drop=True)
    return df


def enrich(df):
    """给每行附上同城市的 IQR 分位与 5 天滚动均值"""
    q1 = df.groupby('city_id')['aqi'].transform(lambda x: x.quantile(0.25))
    q3 = df.groupby('city_id')['aqi'].transform(lambda x: x.quantile(0.75))
    roll = df.groupby('city_id')['aqi'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    df['_q1'] = q1
    df['_q3'] = q3
    df['_roll'] = roll
    return df


def evaluate(df, weights=(70, 15, 5, 10), thresholds=(20, 35, 55)):
    w_exp, w_meteo, w_ano, w_trend = weights
    t_med, t_high, t_severe = thresholds

    rs = []
    for _, row in df.iterrows():
        r = compute_r(row, w_exp, w_meteo, w_ano, w_trend,
                      aqi_bg_q1=row['_q1'], aqi_bg_q3=row['_q3'],
                      rolling_mean=row['_roll'])
        rs.append(r)
    df = df.copy()
    df['r_score'] = rs
    df['r_level'] = df['r_score'].apply(lambda r: r_to_level(r, t_med, t_high, t_severe))
    df['hj_level'] = df['aqi'].apply(aqi_to_hj633_level)

    total = len(df)
    match = (df['r_level'] == df['hj_level']).sum()
    consistency = match / total if total else 0
    # 相邻级别容差一致率（相差 ≤ 1 级也算一致）
    level_order = {'low': 0, 'medium': 1, 'high': 2, 'severe': 3}
    diff = (df['r_level'].map(level_order) - df['hj_level'].map(level_order)).abs()
    near = (diff <= 1).sum() / total if total else 0

    # 混淆矩阵
    cm = pd.crosstab(df['hj_level'], df['r_level'],
                     rownames=['HJ633 实际'], colnames=['R 预测'],
                     dropna=False).reindex(index=['low', 'medium', 'high', 'severe'],
                                           columns=['low', 'medium', 'high', 'severe'],
                                           fill_value=0)
    return {'total': total, 'consistency': consistency, 'near': near, 'cm': cm}


def evaluate_with_split(df, n_train_cities=24, seed=42, weights=(70, 15, 5, 10),
                        candidate_thresholds=None):
    """
    按城市切分 train/test 网格搜索阈值是否过拟合到这批数据。

    流程：
      1) 在 train_cities 上对 candidate_thresholds 网格搜索严格一致率最高的阈值组；
      2) 把该阈值组应用到 test_cities 上重新评估，报告测试集的严格 / 容差一致率；
      3) 同时给出训练集结果作对照。

    若测试集与训练集一致率差距 < 2 个百分点，认为阈值搜索过程未明显过拟合
    """
    if candidate_thresholds is None:
        candidate_thresholds = [
            (18, 33, 53), (20, 35, 55), (22, 37, 57),
            (25, 38, 58), (25, 40, 60), (28, 42, 62), (30, 45, 65),
        ]

    cities = sorted(df['city_id'].unique())
    rng = np.random.default_rng(seed)
    cities_shuffled = list(cities)
    rng.shuffle(cities_shuffled)
    train_cities = set(cities_shuffled[:n_train_cities])
    test_cities = set(cities_shuffled[n_train_cities:])

    train_df = df[df['city_id'].isin(train_cities)].copy()
    test_df = df[df['city_id'].isin(test_cities)].copy()

    # 网格搜索
    best_thr = None
    best_train_consistency = -1.0
    for thr in candidate_thresholds:
        r = evaluate(train_df, weights=weights, thresholds=thr)
        if r['consistency'] > best_train_consistency:
            best_train_consistency = r['consistency']
            best_thr = thr

    train_eval = evaluate(train_df, weights=weights, thresholds=best_thr)
    test_eval = evaluate(test_df, weights=weights, thresholds=best_thr)
    return {
        'train_cities': sorted(train_cities),
        'test_cities': sorted(test_cities),
        'best_thresholds': best_thr,
        'train_consistency': train_eval['consistency'],
        'train_near': train_eval['near'],
        'train_total': train_eval['total'],
        'test_consistency': test_eval['consistency'],
        'test_near': test_eval['near'],
        'test_total': test_eval['total'],
    }


def main():
    app = create_app()
    with app.app_context():
        print('>>> 加载历史记录 ...')
        df = load_records()
        print(f'    共 {len(df)} 条记录，{df.city_id.nunique()} 个城市')
        df = enrich(df)

        print('\n>>> 默认权重评估 (70 / 15 / 5 / 10, 阈值 20 / 35 / 55)')
        res = evaluate(df, weights=(70, 15, 5, 10), thresholds=(20, 35, 55))
        print(f'  严格一致率: {res["consistency"]*100:.2f}%')
        print(f'  容差一致率(±1 级): {res["near"]*100:.2f}%')
        print('  混淆矩阵:')
        print(res['cm'].to_string())

        print('\n>>> 权重敏感性扫描')
        print(f"{'方案':<28}{'一致率':>10}{'±1 级一致率':>14}")
        for weights in [(70, 15, 5, 10), (65, 20, 5, 10), (75, 10, 5, 10),
                        (60, 20, 10, 10), (80, 10, 5, 5)]:
            r = evaluate(df, weights=weights, thresholds=(20, 35, 55))
            tag = f'{weights}'
            print(f"{tag:<28}{r['consistency']*100:>9.2f}%{r['near']*100:>13.2f}%")

        print('\n>>> 分级阈值敏感性扫描 (权重固定 70/15/5/10)')
        print(f"{'阈值':<28}{'一致率':>10}{'±1 级一致率':>14}")
        for thr in [(18, 33, 53), (20, 35, 55), (22, 37, 57), (25, 38, 58),
                    (25, 40, 60), (28, 42, 62), (30, 45, 65), (20, 40, 60), (15, 30, 50)]:
            r = evaluate(df, weights=(70, 15, 5, 10), thresholds=thr)
            tag = f'{thr}'
            print(f"{tag:<28}{r['consistency']*100:>9.2f}%{r['near']*100:>13.2f}%")

        # 论文表 6-8 默认行使用 25/38/58 — 这里的复核必须与论文一致
        print('\n>>> 最终方案复核 (70/15/5/10, 阈值 25 / 38 / 58)')
        best = evaluate(df, weights=(70, 15, 5, 10), thresholds=(25, 38, 58))
        print(f'  严格一致率: {best["consistency"]*100:.2f}%')
        print(f'  ±1 级一致率: {best["near"]*100:.2f}%')
        print('  混淆矩阵:')
        print(best['cm'].to_string())

        # train/test split 
        print('\n>>> Split 验证 (24 城训练 → 10 城测试)')
        split = evaluate_with_split(df, n_train_cities=24, seed=42,
                                    weights=(70, 15, 5, 10))
        print(f'  训练城市数: {len(split["train_cities"])}, 训练样本: {split["train_total"]}')
        print(f'  测试城市数: {len(split["test_cities"])}, 测试样本: {split["test_total"]}')
        print(f'  训练集网格搜索得到的阈值: {split["best_thresholds"]}')
        print(f'  训练集严格一致率: {split["train_consistency"]*100:.2f}%')
        print(f'  训练集 ±1 级一致率: {split["train_near"]*100:.2f}%')
        print(f'  测试集严格一致率: {split["test_consistency"]*100:.2f}%')
        print(f'  测试集 ±1 级一致率: {split["test_near"]*100:.2f}%')
        gap = abs(split['train_consistency'] - split['test_consistency']) * 100
        print(f'  train-test 一致率差距: {gap:.2f} 个百分点 '
              f'({"未明显过拟合" if gap < 2 else ("轻微过拟合" if gap < 5 else "存在过拟合，应在论文中坦白报告")})')

        # 多种子复核：避免 seed=42 偶然好看
        print('\n>>> Split 多种子复核')
        gaps = []
        for seed in (1, 7, 42, 123, 2025):
            sp = evaluate_with_split(df, n_train_cities=24, seed=seed,
                                     weights=(70, 15, 5, 10))
            g = abs(sp['train_consistency'] - sp['test_consistency']) * 100
            gaps.append(g)
            print(f'  seed={seed}: 训练 {sp["train_consistency"]*100:.2f}% / '
                  f'测试 {sp["test_consistency"]*100:.2f}% / 阈值 {sp["best_thresholds"]} / '
                  f'差距 {g:.2f} 点')
        if gaps:
            print(f'  5 种子平均差距: {sum(gaps)/len(gaps):.2f} 个百分点')


if __name__ == '__main__':
    main()
