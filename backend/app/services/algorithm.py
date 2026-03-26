"""
算法模块 - 移动平均预测 + IQR 异常检测
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import AirQualityRecord, PredictionResult, AnomalyEvent

# 支持的预测指标
METRICS = ['aqi', 'pm25', 'pm10', 'so2', 'no2', 'co', 'o3']


# ============================================================
# 1. 移动平均预测 (Moving Average)
# ============================================================

def moving_average_predict(city_id, metric='aqi', window=7, forecast_days=7):
    """
    基于简单移动平均(SMA)对指定城市的某指标进行趋势预测

    参数:
        city_id: 城市ID
        metric: 指标名 (aqi/pm25/pm10/so2/no2/co/o3)
        window: 移动平均窗口大小(天)
        forecast_days: 向后预测天数

    返回:
        {
            'history': [{'date': ..., 'value': ...}, ...],
            'predictions': [{'date': ..., 'predicted': ..., 'upper': ..., 'lower': ...}, ...],
            'mape': float  # 回测误差
        }
    """
    if metric not in METRICS:
        raise ValueError(f'不支持的指标: {metric}')

    # 取最近 window*4 天的历史数据用于计算（足够的回测空间）
    lookback_days = max(window * 4, 60)

    # 以 DB 中该城市最新记录日期为基准（避免数据过期时查不到记录）
    latest = db.session.query(func.max(AirQualityRecord.record_time)).filter(
        AirQualityRecord.city_id == city_id
    ).scalar()
    if not latest:
        return {'history': [], 'predictions': [], 'mape': None}
    start_date = latest - timedelta(days=lookback_days)

    col = getattr(AirQualityRecord, metric)
    rows = db.session.query(
        func.date(AirQualityRecord.record_time).label('date'),
        func.round(func.avg(col), 2).label('value'),
    ).filter(
        AirQualityRecord.city_id == city_id,
        AirQualityRecord.record_time >= start_date,
        col.isnot(None),
    ).group_by(func.date(AirQualityRecord.record_time)) \
     .order_by('date').all()

    if len(rows) < window:
        return {'history': [], 'predictions': [], 'mape': None}

    # 构建 DataFrame
    df = pd.DataFrame([{'date': str(r.date), 'value': float(r.value)} for r in rows])
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').sort_index()

    # 计算移动平均
    df['ma'] = df['value'].rolling(window=window, min_periods=1).mean()

    # 计算移动标准差（用于置信区间）
    df['std'] = df['value'].rolling(window=window, min_periods=1).std().fillna(0)

    # --- 回测: 用最后 window 天验证 MAPE ---
    backtest = df.iloc[-window:]
    if len(backtest) > 0 and backtest['value'].mean() > 0:
        mape = float(np.mean(np.abs(
            (backtest['value'] - backtest['ma']) / backtest['value']
        )) * 100)
    else:
        mape = 0.0

    # --- 预测未来 forecast_days 天 ---
    last_window = df['value'].iloc[-window:].values
    last_std = df['std'].iloc[-1] if df['std'].iloc[-1] > 0 else df['value'].std() * 0.3
    last_date = df.index[-1]

    predictions = []
    rolling_values = list(last_window)

    for i in range(1, forecast_days + 1):
        pred_date = last_date + timedelta(days=i)
        predicted = float(np.mean(rolling_values[-window:]))
        # 置信区间随预测步数扩大
        margin = last_std * (1 + 0.15 * i)
        predictions.append({
            'date': pred_date.strftime('%Y-%m-%d'),
            'predicted': round(predicted, 2),
            'upper': round(predicted + margin, 2),
            'lower': round(max(0, predicted - margin), 2),
        })
        rolling_values.append(predicted)

    # 历史数据
    history = [
        {'date': idx.strftime('%Y-%m-%d'), 'value': round(row['value'], 2), 'ma': round(row['ma'], 2)}
        for idx, row in df.iterrows()
    ]

    return {
        'history': history,
        'predictions': predictions,
        'mape': round(mape, 2),
        'window': window,
    }


def save_predictions(city_id, metric, predictions, window):
    """将预测结果持久化到 prediction_results 表"""
    for p in predictions:
        record = PredictionResult(
            city_id=city_id,
            algorithm_type='moving_average',
            metric_name=metric,
            prediction_date=datetime.strptime(p['date'], '%Y-%m-%d').date(),
            predicted_value=p['predicted'],
            confidence_upper=p['upper'],
            confidence_lower=p['lower'],
            window_size=window,
        )
        db.session.add(record)
    db.session.commit()


# ============================================================
# 2. IQR 异常检测 (Interquartile Range)
# ============================================================

def iqr_detect(city_id, metric='aqi', days=90, multiplier=1.5):
    """
    基于 IQR 检测指定城市某指标的异常值

    参数:
        city_id: 城市ID
        metric: 检测指标
        days: 回溯天数(用于计算 Q1/Q3)
        multiplier: IQR 倍数阈值(1.5=普通异常, 3.0=极端异常)

    返回:
        {
            'q1': float, 'q3': float, 'iqr': float,
            'lower_bound': float, 'upper_bound': float,
            'anomalies': [{'date': ..., 'value': ..., 'type': 'high'|'low', 'severity': ...}, ...]
        }
    """
    if metric not in METRICS:
        raise ValueError(f'不支持的指标: {metric}')

    # 以 DB 最新记录为基准
    latest = db.session.query(func.max(AirQualityRecord.record_time)).filter(
        AirQualityRecord.city_id == city_id
    ).scalar()
    if not latest:
        return {'q1': 0, 'q3': 0, 'iqr': 0, 'lower_bound': 0, 'upper_bound': 0, 'anomalies': []}
    start_date = latest - timedelta(days=days)
    col = getattr(AirQualityRecord, metric)

    rows = db.session.query(
        func.date(AirQualityRecord.record_time).label('date'),
        func.round(func.avg(col), 2).label('value'),
    ).filter(
        AirQualityRecord.city_id == city_id,
        AirQualityRecord.record_time >= start_date,
        col.isnot(None),
    ).group_by(func.date(AirQualityRecord.record_time)) \
     .order_by('date').all()

    if len(rows) < 10:
        return {'q1': 0, 'q3': 0, 'iqr': 0, 'lower_bound': 0, 'upper_bound': 0, 'anomalies': []}

    values = np.array([float(r.value) for r in rows])
    dates = [str(r.date) for r in rows]

    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    iqr = q3 - q1
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    # 极端异常阈值（3倍IQR）
    extreme_lower = q1 - 3.0 * iqr
    extreme_upper = q3 + 3.0 * iqr

    anomalies = []
    for date_str, val in zip(dates, values):
        if val > upper_bound:
            severity = 'severe' if val > extreme_upper else ('moderate' if val > q3 + 2 * iqr else 'mild')
            anomalies.append({
                'date': date_str, 'value': round(float(val), 2),
                'type': 'high', 'severity': severity,
            })
        elif val < lower_bound:
            severity = 'severe' if val < extreme_lower else ('moderate' if val < q1 - 2 * iqr else 'mild')
            anomalies.append({
                'date': date_str, 'value': round(float(val), 2),
                'type': 'low', 'severity': severity,
            })

    return {
        'q1': round(q1, 2),
        'q3': round(q3, 2),
        'iqr': round(iqr, 2),
        'lower_bound': round(lower_bound, 2),
        'upper_bound': round(upper_bound, 2),
        'total_points': len(values),
        'anomaly_count': len(anomalies),
        'anomalies': anomalies,
    }


def save_anomalies(city_id, metric, detect_result):
    """将异常检测结果持久化到 anomaly_events 表"""
    for a in detect_result['anomalies']:
        event = AnomalyEvent(
            city_id=city_id,
            metric_name=metric,
            record_time=datetime.strptime(a['date'], '%Y-%m-%d'),
            actual_value=a['value'],
            q1_value=detect_result['q1'],
            q3_value=detect_result['q3'],
            iqr_value=detect_result['iqr'],
            lower_bound=detect_result['lower_bound'],
            upper_bound=detect_result['upper_bound'],
            anomaly_type=a['type'],
            severity=a['severity'],
        )
        db.session.add(event)
    db.session.commit()


# ============================================================
# 3. 批量运行入口（供 CLI / 定时任务调用）
# ============================================================

def run_all_predictions(window=7, forecast_days=7):
    """对所有城市的 AQI 和 PM2.5 执行预测"""
    from app.models import City
    cities = City.query.all()
    results = []
    for city in cities:
        for metric in ['aqi', 'pm25']:
            pred = moving_average_predict(city.id, metric, window, forecast_days)
            if pred['predictions']:
                save_predictions(city.id, metric, pred['predictions'], window)
                results.append({
                    'city': city.name, 'metric': metric,
                    'mape': pred['mape'], 'forecast_count': len(pred['predictions']),
                })
    return results


def run_all_anomaly_detection(days=90):
    """对所有城市的 AQI 和 PM2.5 执行异常检测"""
    from app.models import City
    cities = City.query.all()
    results = []
    for city in cities:
        for metric in ['aqi', 'pm25']:
            detect = iqr_detect(city.id, metric, days)
            if detect['anomalies']:
                save_anomalies(city.id, metric, detect)
                results.append({
                    'city': city.name, 'metric': metric,
                    'anomaly_count': detect['anomaly_count'],
                })
    return results
