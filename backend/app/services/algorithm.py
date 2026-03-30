"""算法模块 - 多模型预测 + IQR 异常检测 + 综合风险评分"""
import warnings
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import func

from app import db
from app.models import AirQualityRecord, PredictionResult, AnomalyEvent

warnings.filterwarnings('ignore')

PREDICTION_METRICS = ['aqi', 'pm25', 'pm10', 'o3']
METRICS = ['aqi', 'pm25', 'pm10', 'so2', 'no2', 'co', 'o3']
SUPPORTED_ALGORITHMS = ['moving_average', 'arima', 'lstm']


# ============================================================
# 基础工具
# ============================================================

def _validate_metric(metric, allowed_metrics=None):
    allowed = allowed_metrics or METRICS
    if metric not in allowed:
        raise ValueError(f'不支持的指标: {metric}')


def _get_daily_series(city_id, metric='aqi', lookback_days=180):
    _validate_metric(metric)
    latest = db.session.query(func.max(AirQualityRecord.record_time)).filter(
        AirQualityRecord.city_id == city_id
    ).scalar()
    if not latest:
        return pd.DataFrame(columns=['value'])

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

    if not rows:
        return pd.DataFrame(columns=['value'])

    df = pd.DataFrame([{'date': str(r.date), 'value': float(r.value)} for r in rows])
    df['date'] = pd.to_datetime(df['date'])
    return df.set_index('date').sort_index()


def _build_history(df, reference_series=None, reference_key='ma'):
    history = []
    for idx, row in df.iterrows():
        item = {
            'date': idx.strftime('%Y-%m-%d'),
            'value': round(float(row['value']), 2),
        }
        if reference_series is not None:
            ref_val = reference_series.loc[idx] if idx in reference_series.index else None
            item[reference_key] = round(float(ref_val), 2) if pd.notna(ref_val) else None
        history.append(item)
    return history


def _calculate_bounds(predictions, margin_base):
    result = []
    for idx, item in enumerate(predictions, start=1):
        margin = float(margin_base) * (1 + 0.15 * idx)
        result.append({
            'date': item['date'],
            'predicted': round(float(item['predicted']), 2),
            'upper': round(float(item['predicted'] + margin), 2),
            'lower': round(max(0.0, float(item['predicted'] - margin)), 2),
        })
    return result


def evaluate_forecast(actual, predicted):
    actual_arr = np.asarray(actual, dtype=float)
    pred_arr = np.asarray(predicted, dtype=float)
    mask = ~(np.isnan(actual_arr) | np.isnan(pred_arr))
    actual_arr = actual_arr[mask]
    pred_arr = pred_arr[mask]

    if len(actual_arr) == 0:
        return {'mae': None, 'rmse': None, 'mape': None, 'r2': None}

    diff = actual_arr - pred_arr
    mae = float(np.mean(np.abs(diff)))
    rmse = float(np.sqrt(np.mean(diff ** 2)))

    non_zero = actual_arr != 0
    if np.any(non_zero):
        mape = float(np.mean(np.abs(diff[non_zero] / actual_arr[non_zero])) * 100)
    else:
        mape = None

    ss_res = float(np.sum(diff ** 2))
    ss_tot = float(np.sum((actual_arr - np.mean(actual_arr)) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else None

    return {
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'mape': round(mape, 2) if mape is not None else None,
        'r2': round(r2, 4) if r2 is not None else None,
    }


def _empty_prediction_result(metric, algorithm, forecast_days, window, fallback=False, reason=None):
    return {
        'metric': metric,
        'selectedAlgorithm': algorithm,
        'requestedAlgorithm': algorithm,
        'history': [],
        'predictions': [],
        'evaluation': {'mae': None, 'rmse': None, 'mape': None, 'r2': None},
        'window': window,
        'forecastDays': forecast_days,
        'usedFallback': fallback,
        'fallbackReason': reason,
        'comparison': [],
    }


def _fallback_result(df, metric, algorithm, forecast_days, window, reason=None):
    if df.empty:
        return _empty_prediction_result(metric, algorithm, forecast_days, window, True, reason)
    base = moving_average_predict(
        city_id=None,
        metric=metric,
        window=window,
        forecast_days=forecast_days,
        prepared_df=df,
    )
    base['requestedAlgorithm'] = algorithm
    base['selectedAlgorithm'] = algorithm
    base['usedFallback'] = True
    base['fallbackReason'] = reason or '数据不足或依赖缺失，已回退到移动平均'
    return base


# ============================================================
# 1. 多模型预测
# ============================================================

def moving_average_predict(city_id, metric='aqi', window=7, forecast_days=7, prepared_df=None):
    _validate_metric(metric, PREDICTION_METRICS)
    lookback_days = max(window * 6, 90)
    df = prepared_df.copy() if prepared_df is not None else _get_daily_series(city_id, metric, lookback_days)
    if len(df) < window:
        return _empty_prediction_result(metric, 'moving_average', forecast_days, window)

    rolling_ma = df['value'].rolling(window=window, min_periods=1).mean()
    rolling_std = df['value'].rolling(window=window, min_periods=1).std().fillna(0)

    test_size = min(max(forecast_days, 5), max(len(df) // 4, 1))
    if len(df) <= test_size:
        test_size = max(1, len(df) - 1)
    train_values = df['value'].iloc[:-test_size].tolist()
    actual_test = df['value'].iloc[-test_size:].tolist()

    if not train_values:
        train_values = df['value'].iloc[:-1].tolist() or df['value'].tolist()
        actual_test = df['value'].iloc[-1:].tolist()

    backtest_pred = []
    rolling_values = list(train_values)
    for actual in actual_test:
        pred = float(np.mean(rolling_values[-window:]))
        backtest_pred.append(pred)
        rolling_values.append(actual)

    evaluation = evaluate_forecast(actual_test, backtest_pred)

    last_window = df['value'].iloc[-window:].tolist()
    last_std = float(rolling_std.iloc[-1]) if float(rolling_std.iloc[-1]) > 0 else float(df['value'].std() or 1) * 0.3
    last_date = df.index[-1]
    forecast = []
    rolling_forecast_values = list(last_window)
    for step in range(1, forecast_days + 1):
        pred = float(np.mean(rolling_forecast_values[-window:]))
        forecast.append({
            'date': (last_date + timedelta(days=step)).strftime('%Y-%m-%d'),
            'predicted': pred,
        })
        rolling_forecast_values.append(pred)

    return {
        'metric': metric,
        'selectedAlgorithm': 'moving_average',
        'requestedAlgorithm': 'moving_average',
        'history': _build_history(df, rolling_ma, 'ma'),
        'predictions': _calculate_bounds(forecast, last_std),
        'evaluation': evaluation,
        'window': window,
        'forecastDays': forecast_days,
        'usedFallback': False,
        'comparison': [],
    }


def arima_predict(city_id, metric='aqi', window=7, forecast_days=7, prepared_df=None):
    _validate_metric(metric, PREDICTION_METRICS)
    df = prepared_df.copy() if prepared_df is not None else _get_daily_series(city_id, metric, 240)
    if len(df) < max(20, forecast_days * 3):
        return _fallback_result(df, metric, 'arima', forecast_days, window, 'ARIMA 所需历史数据不足')

    try:
        from statsmodels.tsa.arima.model import ARIMA
    except Exception:
        return _fallback_result(df, metric, 'arima', forecast_days, window, '未安装 statsmodels，已回退到移动平均')

    test_size = min(max(forecast_days, 5), max(len(df) // 5, 1))
    train = df['value'].iloc[:-test_size]
    test = df['value'].iloc[-test_size:]
    if len(train) < 10:
        return _fallback_result(df, metric, 'arima', forecast_days, window, 'ARIMA 训练样本不足')

    best_model = None
    best_order = None
    best_aic = None
    for order in [(1, 1, 1), (2, 1, 1), (1, 1, 2), (2, 1, 2)]:
        try:
            model = ARIMA(train, order=order).fit()
            if best_aic is None or model.aic < best_aic:
                best_model = model
                best_order = order
                best_aic = model.aic
        except Exception:
            continue

    if best_model is None:
        return _fallback_result(df, metric, 'arima', forecast_days, window, 'ARIMA 拟合失败，已回退到移动平均')

    backtest_pred = best_model.forecast(steps=len(test))
    evaluation = evaluate_forecast(test.values, backtest_pred.values)

    final_model = ARIMA(df['value'], order=best_order).fit()
    forecast_res = final_model.get_forecast(steps=forecast_days)
    predicted_mean = forecast_res.predicted_mean
    conf_int = forecast_res.conf_int(alpha=0.2)
    lower_col = conf_int.columns[0]
    upper_col = conf_int.columns[1]
    last_date = df.index[-1]

    predictions = []
    for step in range(1, forecast_days + 1):
        predictions.append({
            'date': (last_date + timedelta(days=step)).strftime('%Y-%m-%d'),
            'predicted': round(float(predicted_mean.iloc[step - 1]), 2),
            'upper': round(float(conf_int.iloc[step - 1][upper_col]), 2),
            'lower': round(max(0.0, float(conf_int.iloc[step - 1][lower_col])), 2),
        })

    fitted = final_model.fittedvalues.reindex(df.index)
    return {
        'metric': metric,
        'selectedAlgorithm': 'arima',
        'requestedAlgorithm': 'arima',
        'history': _build_history(df, fitted, 'ma'),
        'predictions': predictions,
        'evaluation': evaluation,
        'window': window,
        'forecastDays': forecast_days,
        'modelInfo': {'order': list(best_order)},
        'usedFallback': False,
        'comparison': [],
    }


def lstm_predict(city_id, metric='aqi', window=7, forecast_days=7, prepared_df=None):
    _validate_metric(metric, PREDICTION_METRICS)
    df = prepared_df.copy() if prepared_df is not None else _get_daily_series(city_id, metric, 240)
    lookback = max(window, 7)
    if len(df) < max(40, lookback * 4):
        return _fallback_result(df, metric, 'lstm', forecast_days, window, 'LSTM 所需历史数据不足')

    try:
        from tensorflow.keras import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Input
        from tensorflow.keras.optimizers import Adam
        import tensorflow as tf
    except Exception:
        return _fallback_result(df, metric, 'lstm', forecast_days, window, '未安装 TensorFlow，已回退到移动平均')

    tf.random.set_seed(42)
    np.random.seed(42)

    values = df['value'].values.astype(float)
    min_val = float(np.min(values))
    max_val = float(np.max(values))
    scale = max(max_val - min_val, 1.0)
    normalized = (values - min_val) / scale

    def make_sequences(series):
        x, y = [], []
        for i in range(len(series) - lookback):
            x.append(series[i:i + lookback])
            y.append(series[i + lookback])
        return np.array(x), np.array(y)

    x_all, y_all = make_sequences(normalized)
    if len(x_all) < 12:
        return _fallback_result(df, metric, 'lstm', forecast_days, window, 'LSTM 序列样本不足')

    split_idx = max(int(len(x_all) * 0.8), 1)
    x_train, y_train = x_all[:split_idx], y_all[:split_idx]
    x_test, y_test = x_all[split_idx:], y_all[split_idx:]
    if len(x_test) == 0:
        x_test, y_test = x_all[-1:], y_all[-1:]
        x_train, y_train = x_all[:-1], y_all[:-1]

    x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], 1))
    x_test = x_test.reshape((x_test.shape[0], x_test.shape[1], 1))

    model = Sequential([
        Input(shape=(lookback, 1)),
        LSTM(32),
        Dense(16, activation='relu'),
        Dense(1),
    ])
    model.compile(optimizer=Adam(learning_rate=0.01), loss='mse')
    model.fit(x_train, y_train, epochs=25, batch_size=8, verbose=0)

    test_pred = model.predict(x_test, verbose=0).reshape(-1)
    evaluation = evaluate_forecast(y_test * scale + min_val, test_pred * scale + min_val)

    rolling_input = normalized[-lookback:].tolist()
    forecast = []
    for step in range(1, forecast_days + 1):
        x_input = np.array(rolling_input[-lookback:]).reshape((1, lookback, 1))
        pred_norm = float(model.predict(x_input, verbose=0).reshape(-1)[0])
        pred_value = pred_norm * scale + min_val
        forecast.append({
            'date': (df.index[-1] + timedelta(days=step)).strftime('%Y-%m-%d'),
            'predicted': pred_value,
        })
        rolling_input.append(pred_norm)

    history_pred = model.predict(x_all.reshape((x_all.shape[0], x_all.shape[1], 1)), verbose=0).reshape(-1)
    history_ref = pd.Series(index=df.index, dtype=float)
    history_ref.iloc[lookback:] = history_pred * scale + min_val
    margin_base = float(np.std(values[-max(lookback, 10):]) or 1) * 0.35

    return {
        'metric': metric,
        'selectedAlgorithm': 'lstm',
        'requestedAlgorithm': 'lstm',
        'history': _build_history(df, history_ref, 'ma'),
        'predictions': _calculate_bounds(forecast, margin_base),
        'evaluation': evaluation,
        'window': window,
        'forecastDays': forecast_days,
        'modelInfo': {'lookback': lookback, 'epochs': 25},
        'usedFallback': False,
        'comparison': [],
    }


def run_prediction_pipeline(city_id, metric='aqi', algorithm='moving_average', window=7, forecast_days=7, compare=False):
    _validate_metric(metric, PREDICTION_METRICS)
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f'不支持的算法: {algorithm}')

    prepared_df = _get_daily_series(city_id, metric, max(240, window * 8))
    predictors = {
        'moving_average': moving_average_predict,
        'arima': arima_predict,
        'lstm': lstm_predict,
    }

    result = predictors[algorithm](city_id, metric, window, forecast_days, prepared_df=prepared_df)
    result['requestedAlgorithm'] = algorithm
    result['selectedAlgorithm'] = result.get('selectedAlgorithm', algorithm)

    if compare:
        comparison = []
        for algo in SUPPORTED_ALGORITHMS:
            algo_result = predictors[algo](city_id, metric, window, forecast_days, prepared_df=prepared_df)
            comparison.append({
                'algorithm': algo,
                **algo_result.get('evaluation', {}),
                'usedFallback': algo_result.get('usedFallback', False),
            })
        result['comparison'] = comparison
    else:
        result['comparison'] = []

    return result


def save_predictions(city_id, metric, predictions, window, algorithm='moving_average', evaluation=None):
    """将预测结果持久化到 prediction_results 表"""
    mape = evaluation.get('mape') if evaluation else None
    for p in predictions:
        record = PredictionResult(
            city_id=city_id,
            algorithm_type=algorithm,
            metric_name=metric,
            prediction_date=datetime.strptime(p['date'], '%Y-%m-%d').date(),
            predicted_value=p['predicted'],
            confidence_upper=p.get('upper'),
            confidence_lower=p.get('lower'),
            window_size=window,
            mape=mape,
        )
        db.session.add(record)
    db.session.commit()


# ============================================================
# 2. IQR 异常检测 (Interquartile Range)
# ============================================================

def iqr_detect(city_id, metric='aqi', days=90, multiplier=1.5):
    _validate_metric(metric)

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
    extreme_lower = q1 - 3.0 * iqr
    extreme_upper = q3 + 3.0 * iqr

    anomalies = []
    for date_str, val in zip(dates, values):
        if val > upper_bound:
            severity = 'severe' if val > extreme_upper else ('moderate' if val > q3 + 2 * iqr else 'mild')
            anomalies.append({
                'date': date_str,
                'value': round(float(val), 2),
                'type': 'high',
                'severity': severity,
            })
        elif val < lower_bound:
            severity = 'severe' if val < extreme_lower else ('moderate' if val < q1 - 2 * iqr else 'mild')
            anomalies.append({
                'date': date_str,
                'value': round(float(val), 2),
                'type': 'low',
                'severity': severity,
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


def calculate_risk_score(city_id, forecast_days=5):
    base_df = _get_daily_series(city_id, 'aqi', 30)
    if base_df.empty:
        return {
            'score': 0,
            'level': 'low',
            'summary': '暂无可用数据',
            'drivers': [],
            'futureRisk': [],
            'iqrSignals': {},
            'metricPredictions': {},
        }

    latest_record = AirQualityRecord.query.filter_by(city_id=city_id) \
        .order_by(AirQualityRecord.record_time.desc()).first()
    if not latest_record:
        return {
            'score': 0,
            'level': 'low',
            'summary': '暂无可用数据',
            'drivers': [],
            'futureRisk': [],
            'iqrSignals': {},
            'metricPredictions': {},
        }

    def clamp_score(value, good, bad):
        if value is None:
            return 0.0
        score = (float(value) - good) / (bad - good) * 100
        return float(min(100, max(0, score)))

    pollution_scores = {
        'aqi': clamp_score(latest_record.aqi, 50, 200),
        'pm25': clamp_score(latest_record.pm25, 35, 150),
        'pm10': clamp_score(latest_record.pm10, 50, 250),
        'o3': clamp_score(latest_record.o3, 100, 260),
    }
    weather_scores = {
        'humidity': clamp_score(latest_record.humidity, 40, 90),
        'wind_speed': 100 - clamp_score(latest_record.wind_speed, 2, 8),
        'rainfall': 100 - clamp_score(latest_record.rainfall, 0, 10),
        'temperature': clamp_score(latest_record.temperature, 10, 35) * 0.4,
    }

    pollution_total = (
        pollution_scores['aqi'] * 0.28 +
        pollution_scores['pm25'] * 0.22 +
        pollution_scores['pm10'] * 0.16 +
        pollution_scores['o3'] * 0.14
    )
    weather_total = (
        weather_scores['humidity'] * 0.08 +
        weather_scores['wind_speed'] * 0.08 +
        weather_scores['rainfall'] * 0.05 +
        weather_scores['temperature'] * 0.04
    )

    iqr_signals = {}
    anomaly_boost = 0.0
    for metric in ['aqi', 'pm25', 'pm10', 'o3']:
        detect = iqr_detect(city_id, metric=metric, days=60)
        signal_count = detect['anomaly_count']
        iqr_signals[metric] = signal_count
        anomaly_boost += min(8, signal_count * 2)

    score = min(100, round(pollution_total + weather_total + anomaly_boost, 2))
    if score >= 70:
        level = 'severe'
    elif score >= 50:
        level = 'high'
    elif score >= 30:
        level = 'medium'
    else:
        level = 'low'

    drivers = [
        {'factor': key, 'value': round(float(getattr(latest_record, key) or 0), 2), 'contribution': round(val, 2)}
        for key, val in {
            'aqi': pollution_scores['aqi'] * 0.28,
            'pm25': pollution_scores['pm25'] * 0.22,
            'pm10': pollution_scores['pm10'] * 0.16,
            'o3': pollution_scores['o3'] * 0.14,
            'humidity': weather_scores['humidity'] * 0.08,
            'wind_speed': weather_scores['wind_speed'] * 0.08,
        }.items()
    ]
    drivers.sort(key=lambda x: x['contribution'], reverse=True)

    metric_predictions = {}
    future_risk = []
    for metric in PREDICTION_METRICS:
        pred = run_prediction_pipeline(city_id, metric=metric, algorithm='moving_average', forecast_days=forecast_days, compare=False)
        metric_predictions[metric] = pred.get('predictions', [])

    for idx in range(forecast_days):
        aqi_pred = metric_predictions['aqi'][idx]['predicted'] if idx < len(metric_predictions['aqi']) else (latest_record.aqi or 0)
        pm25_pred = metric_predictions['pm25'][idx]['predicted'] if idx < len(metric_predictions['pm25']) else float(latest_record.pm25 or 0)
        pm10_pred = metric_predictions['pm10'][idx]['predicted'] if idx < len(metric_predictions['pm10']) else float(latest_record.pm10 or 0)
        o3_pred = metric_predictions['o3'][idx]['predicted'] if idx < len(metric_predictions['o3']) else float(latest_record.o3 or 0)
        day_score = min(100, round(
            clamp_score(aqi_pred, 50, 200) * 0.35 +
            clamp_score(pm25_pred, 35, 150) * 0.25 +
            clamp_score(pm10_pred, 50, 250) * 0.2 +
            clamp_score(o3_pred, 100, 260) * 0.2,
            2,
        ))
        if day_score >= 70:
            day_level = 'severe'
        elif day_score >= 50:
            day_level = 'high'
        elif day_score >= 30:
            day_level = 'medium'
        else:
            day_level = 'low'
        date = metric_predictions['aqi'][idx]['date'] if idx < len(metric_predictions['aqi']) else None
        future_risk.append({'date': date, 'score': day_score, 'level': day_level})

    summary = f"当前综合风险为{level}，主要受{drivers[0]['factor']}和{drivers[1]['factor'] if len(drivers) > 1 else drivers[0]['factor']}影响。"
    return {
        'score': score,
        'level': level,
        'summary': summary,
        'drivers': drivers[:5],
        'futureRisk': future_risk,
        'iqrSignals': iqr_signals,
        'metricPredictions': metric_predictions,
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

def run_all_predictions(window=7, forecast_days=7, algorithm='moving_average'):
    """对所有城市的 AQI 和 PM2.5 执行预测"""
    from app.models import City
    cities = City.query.all()
    results = []
    for city in cities:
        for metric in ['aqi', 'pm25']:
            pred = run_prediction_pipeline(city.id, metric, algorithm, window, forecast_days, compare=False)
            if pred['predictions']:
                save_predictions(city.id, metric, pred['predictions'], window, pred['selectedAlgorithm'], pred.get('evaluation'))
                results.append({
                    'city': city.name,
                    'metric': metric,
                    'algorithm': pred['selectedAlgorithm'],
                    'mape': pred.get('evaluation', {}).get('mape'),
                    'forecast_count': len(pred['predictions']),
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
                    'city': city.name,
                    'metric': metric,
                    'anomaly_count': detect['anomaly_count'],
                })
    return results
