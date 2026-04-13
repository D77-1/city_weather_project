"""算法模块 - 多模型预测 + 多方法异常检测 + 可解释风险评分"""
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
SUPPORTED_ALGORITHMS = [
    'moving_average',
    'weighted_moving_average',
    'linear_regression',
    'holt_winters',
    'arima',
    'lstm',
]
SUPPORTED_ANOMALY_METHODS = ['iqr', 'zscore', 'mad']


# ============================================================
# 基础工具
# ============================================================


def _validate_metric(metric, allowed_metrics=None):
    allowed = allowed_metrics or METRICS
    if metric not in allowed:
        raise ValueError(f'不支持的指标: {metric}')



def _safe_round(value, digits=2):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return round(float(value), digits)



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



def _series_summary(df):
    if df.empty:
        return {
            'historyStart': None,
            'historyEnd': None,
            'historyDays': 0,
            'source': 'local_db_daily_avg',
        }
    return {
        'historyStart': df.index[0].strftime('%Y-%m-%d'),
        'historyEnd': df.index[-1].strftime('%Y-%m-%d'),
        'historyDays': int(len(df)),
        'source': 'local_db_daily_avg',
    }



def _build_history(df, reference_series=None, reference_key='reference'):
    history = []
    for idx, row in df.iterrows():
        item = {
            'date': idx.strftime('%Y-%m-%d'),
            'value': _safe_round(row['value']),
        }
        if reference_series is not None:
            ref_val = reference_series.loc[idx] if idx in reference_series.index else None
            item[reference_key] = _safe_round(ref_val)
        history.append(item)
    return history



def _calculate_bounds(predictions, margin_base):
    result = []
    margin_base = float(max(margin_base or 0, 1.0))
    for idx, item in enumerate(predictions, start=1):
        margin = margin_base * (1 + 0.12 * idx)
        result.append({
            'date': item['date'],
            'predicted': _safe_round(item['predicted']),
            'upper': _safe_round(item['predicted'] + margin),
            'lower': _safe_round(max(0.0, float(item['predicted'] - margin))),
        })
    return result



def _future_dates(last_date, forecast_days):
    return [(last_date + timedelta(days=step)).strftime('%Y-%m-%d') for step in range(1, forecast_days + 1)]



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
        'mae': _safe_round(mae),
        'rmse': _safe_round(rmse),
        'mape': _safe_round(mape),
        'r2': _safe_round(r2, 4),
    }



def _algorithm_availability():
    availability = {
        'moving_average': {'available': True, 'reason': '内置算法，无额外依赖'},
        'weighted_moving_average': {'available': True, 'reason': '内置算法，无额外依赖'},
        'linear_regression': {'available': True, 'reason': '基于 Numpy 线性回归'},
        'holt_winters': {'available': True, 'reason': '简化指数平滑实现'},
        'arima': {'available': False, 'reason': '未检测到 statsmodels'},
        'lstm': {'available': False, 'reason': '未检测到 TensorFlow'},
    }

    try:
        from statsmodels.tsa.arima.model import ARIMA  # noqa: F401
        availability['arima'] = {'available': True, 'reason': '已检测到 statsmodels'}
    except Exception:
        pass

    try:
        import tensorflow as tf  # noqa: F401
        availability['lstm'] = {'available': True, 'reason': '已检测到 TensorFlow'}
    except Exception:
        pass

    return availability



def _empty_prediction_result(metric, requested_algorithm, forecast_days, window, df=None, reason=None):
    summary = _series_summary(df if df is not None else pd.DataFrame(columns=['value']))
    return {
        'metric': metric,
        'requestedAlgorithm': requested_algorithm,
        'selectedAlgorithm': requested_algorithm,
        'history': [],
        'predictions': [],
        'evaluation': {'mae': None, 'rmse': None, 'mape': None, 'r2': None},
        'window': window,
        'forecastDays': forecast_days,
        'usedFallback': False,
        'fallbackReason': reason,
        'algorithmStatus': 'unavailable' if reason else 'ok',
        'referenceLabel': '参考线',
        'comparison': [],
        **summary,
    }



def _fallback_result(df, metric, requested_algorithm, forecast_days, window, reason=None):
    if df.empty:
        result = _empty_prediction_result(metric, requested_algorithm, forecast_days, window, df, reason)
        result['usedFallback'] = True
        result['selectedAlgorithm'] = 'moving_average'
        result['algorithmStatus'] = 'fallback'
        return result

    base = moving_average_predict(
        city_id=None,
        metric=metric,
        window=window,
        forecast_days=forecast_days,
        prepared_df=df,
    )
    base['requestedAlgorithm'] = requested_algorithm
    base['selectedAlgorithm'] = 'moving_average'
    base['usedFallback'] = True
    base['fallbackReason'] = reason or '已回退到移动平均'
    base['algorithmStatus'] = 'fallback'
    return base



def _build_result(metric, requested_algorithm, actual_algorithm, forecast_days, window, df, history, predictions,
                  evaluation, reference_label='参考线', used_fallback=False, fallback_reason=None,
                  algorithm_status='ok', extra=None):
    result = {
        'metric': metric,
        'requestedAlgorithm': requested_algorithm,
        'selectedAlgorithm': actual_algorithm,
        'history': history,
        'predictions': predictions,
        'evaluation': evaluation,
        'window': window,
        'forecastDays': forecast_days,
        'usedFallback': used_fallback,
        'fallbackReason': fallback_reason,
        'algorithmStatus': algorithm_status,
        'referenceLabel': reference_label,
        'comparison': [],
        **_series_summary(df),
    }
    if extra:
        result.update(extra)
    return result


# ============================================================
# 1. 多模型预测
# ============================================================


def moving_average_predict(city_id, metric='aqi', window=7, forecast_days=7, prepared_df=None):
    _validate_metric(metric, PREDICTION_METRICS)
    lookback_days = max(window * 6, 90)
    df = prepared_df.copy() if prepared_df is not None else _get_daily_series(city_id, metric, lookback_days)
    if len(df) < window:
        return _empty_prediction_result(metric, 'moving_average', forecast_days, window, df, '历史数据不足')

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

    forecast = []
    rolling_forecast_values = list(last_window)
    for date_str in _future_dates(df.index[-1], forecast_days):
        pred = float(np.mean(rolling_forecast_values[-window:]))
        forecast.append({'date': date_str, 'predicted': pred})
        rolling_forecast_values.append(pred)

    return _build_result(
        metric=metric,
        requested_algorithm='moving_average',
        actual_algorithm='moving_average',
        forecast_days=forecast_days,
        window=window,
        df=df,
        history=_build_history(df, rolling_ma, 'reference'),
        predictions=_calculate_bounds(forecast, last_std),
        evaluation=evaluation,
        reference_label='移动平均参考线',
    )



def weighted_moving_average_predict(city_id, metric='aqi', window=7, forecast_days=7, prepared_df=None):
    _validate_metric(metric, PREDICTION_METRICS)
    df = prepared_df.copy() if prepared_df is not None else _get_daily_series(city_id, metric, max(window * 6, 90))
    if len(df) < window:
        return _empty_prediction_result(metric, 'weighted_moving_average', forecast_days, window, df, '历史数据不足')

    weights = np.arange(1, window + 1, dtype=float)
    weights /= weights.sum()

    def weighted_avg(values):
        arr = np.asarray(values[-window:], dtype=float)
        w = weights[-len(arr):]
        w = w / w.sum()
        return float(np.dot(arr, w))

    ref_series = pd.Series(index=df.index, dtype=float)
    values_list = df['value'].tolist()
    for i in range(len(values_list)):
        subset = values_list[max(0, i - window + 1):i + 1]
        local_weights = np.arange(1, len(subset) + 1, dtype=float)
        local_weights /= local_weights.sum()
        ref_series.iloc[i] = float(np.dot(np.asarray(subset, dtype=float), local_weights))

    test_size = min(max(forecast_days, 5), max(len(df) // 4, 1))
    train_values = values_list[:-test_size] if len(values_list) > test_size else values_list[:-1]
    actual_test = values_list[-test_size:] if len(values_list) > test_size else values_list[-1:]
    if not train_values:
        train_values = values_list[:-1] or values_list
        actual_test = values_list[-1:]

    backtest_pred = []
    rolling_values = list(train_values)
    for actual in actual_test:
        pred = weighted_avg(rolling_values)
        backtest_pred.append(pred)
        rolling_values.append(actual)

    evaluation = evaluate_forecast(actual_test, backtest_pred)
    margin_base = float(df['value'].tail(window).std() or 1) * 0.32
    forecast = []
    rolling_forecast_values = values_list.copy()
    for date_str in _future_dates(df.index[-1], forecast_days):
        pred = weighted_avg(rolling_forecast_values)
        forecast.append({'date': date_str, 'predicted': pred})
        rolling_forecast_values.append(pred)

    return _build_result(
        metric=metric,
        requested_algorithm='weighted_moving_average',
        actual_algorithm='weighted_moving_average',
        forecast_days=forecast_days,
        window=window,
        df=df,
        history=_build_history(df, ref_series, 'reference'),
        predictions=_calculate_bounds(forecast, margin_base),
        evaluation=evaluation,
        reference_label='加权移动平均',
    )



def linear_regression_predict(city_id, metric='aqi', window=7, forecast_days=7, prepared_df=None):
    _validate_metric(metric, PREDICTION_METRICS)
    df = prepared_df.copy() if prepared_df is not None else _get_daily_series(city_id, metric, 180)
    if len(df) < max(12, window + 3):
        return _empty_prediction_result(metric, 'linear_regression', forecast_days, window, df, '历史数据不足')

    values = df['value'].values.astype(float)
    x = np.arange(len(values), dtype=float)
    slope, intercept = np.polyfit(x, values, 1)
    fitted = intercept + slope * x

    test_size = min(max(forecast_days, 5), max(len(df) // 4, 1))
    train_x = x[:-test_size] if len(x) > test_size else x[:-1]
    train_y = values[:-test_size] if len(values) > test_size else values[:-1]
    test_x = x[-test_size:] if len(x) > test_size else x[-1:]
    test_y = values[-test_size:] if len(values) > test_size else values[-1:]
    if len(train_x) < 2:
        return _fallback_result(df, metric, 'linear_regression', forecast_days, window, '线性回归训练样本不足')

    train_slope, train_intercept = np.polyfit(train_x, train_y, 1)
    backtest_pred = train_intercept + train_slope * test_x
    evaluation = evaluate_forecast(test_y, backtest_pred)

    forecast = []
    for step, date_str in enumerate(_future_dates(df.index[-1], forecast_days), start=1):
        pred_x = len(values) + step - 1
        pred = intercept + slope * pred_x
        forecast.append({'date': date_str, 'predicted': max(0.0, float(pred))})

    margin_base = float(np.std(values - fitted) or np.std(values[-window:]) or 1) * 0.9
    fitted_series = pd.Series(fitted, index=df.index)
    return _build_result(
        metric=metric,
        requested_algorithm='linear_regression',
        actual_algorithm='linear_regression',
        forecast_days=forecast_days,
        window=window,
        df=df,
        history=_build_history(df, fitted_series, 'reference'),
        predictions=_calculate_bounds(forecast, margin_base),
        evaluation=evaluation,
        reference_label='线性趋势拟合',
    )



def holt_winters_predict(city_id, metric='aqi', window=7, forecast_days=7, prepared_df=None):
    _validate_metric(metric, PREDICTION_METRICS)
    df = prepared_df.copy() if prepared_df is not None else _get_daily_series(city_id, metric, 180)
    if len(df) < max(10, window + 2):
        return _empty_prediction_result(metric, 'holt_winters', forecast_days, window, df, '历史数据不足')

    values = df['value'].values.astype(float)
    alpha = 0.45
    beta = 0.2
    level = values[0]
    trend = values[1] - values[0] if len(values) > 1 else 0.0
    fitted_values = [level]
    for val in values[1:]:
        prev_level = level
        level = alpha * val + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        fitted_values.append(level + trend)

    test_size = min(max(forecast_days, 5), max(len(values) // 4, 1))
    train_vals = values[:-test_size] if len(values) > test_size else values[:-1]
    test_vals = values[-test_size:] if len(values) > test_size else values[-1:]
    if len(train_vals) < 2:
        return _fallback_result(df, metric, 'holt_winters', forecast_days, window, '指数平滑训练样本不足')

    train_level = train_vals[0]
    train_trend = train_vals[1] - train_vals[0] if len(train_vals) > 1 else 0.0
    backtest_pred = []
    for actual in test_vals:
        pred = train_level + train_trend
        backtest_pred.append(pred)
        prev_level = train_level
        train_level = alpha * actual + (1 - alpha) * (train_level + train_trend)
        train_trend = beta * (train_level - prev_level) + (1 - beta) * train_trend
    evaluation = evaluate_forecast(test_vals, backtest_pred)

    forecast = []
    for step, date_str in enumerate(_future_dates(df.index[-1], forecast_days), start=1):
        pred = level + step * trend
        forecast.append({'date': date_str, 'predicted': max(0.0, float(pred))})

    fitted_series = pd.Series(fitted_values, index=df.index)
    margin_base = float(np.std(values - np.asarray(fitted_values)) or np.std(values[-window:]) or 1) * 0.85
    return _build_result(
        metric=metric,
        requested_algorithm='holt_winters',
        actual_algorithm='holt_winters',
        forecast_days=forecast_days,
        window=window,
        df=df,
        history=_build_history(df, fitted_series, 'reference'),
        predictions=_calculate_bounds(forecast, margin_base),
        evaluation=evaluation,
        reference_label='指数平滑拟合',
    )



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

    predictions = []
    for idx, date_str in enumerate(_future_dates(df.index[-1], forecast_days)):
        predictions.append({
            'date': date_str,
            'predicted': _safe_round(predicted_mean.iloc[idx]),
            'upper': _safe_round(conf_int.iloc[idx][upper_col]),
            'lower': _safe_round(max(0.0, float(conf_int.iloc[idx][lower_col]))),
        })

    fitted = final_model.fittedvalues.reindex(df.index)
    return _build_result(
        metric=metric,
        requested_algorithm='arima',
        actual_algorithm='arima',
        forecast_days=forecast_days,
        window=window,
        df=df,
        history=_build_history(df, fitted, 'reference'),
        predictions=predictions,
        evaluation=evaluation,
        reference_label='ARIMA 历史拟合',
        extra={'modelInfo': {'order': list(best_order)}},
    )



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
    for date_str in _future_dates(df.index[-1], forecast_days):
        x_input = np.array(rolling_input[-lookback:]).reshape((1, lookback, 1))
        pred_norm = float(model.predict(x_input, verbose=0).reshape(-1)[0])
        pred_value = pred_norm * scale + min_val
        forecast.append({'date': date_str, 'predicted': pred_value})
        rolling_input.append(pred_norm)

    history_pred = model.predict(x_all.reshape((x_all.shape[0], x_all.shape[1], 1)), verbose=0).reshape(-1)
    history_ref = pd.Series(index=df.index, dtype=float)
    history_ref.iloc[lookback:] = history_pred * scale + min_val
    margin_base = float(np.std(values[-max(lookback, 10):]) or 1) * 0.35

    return _build_result(
        metric=metric,
        requested_algorithm='lstm',
        actual_algorithm='lstm',
        forecast_days=forecast_days,
        window=window,
        df=df,
        history=_build_history(df, history_ref, 'reference'),
        predictions=_calculate_bounds(forecast, margin_base),
        evaluation=evaluation,
        reference_label='LSTM 历史拟合',
        extra={'modelInfo': {'lookback': lookback, 'epochs': 25}},
    )



def run_prediction_pipeline(city_id, metric='aqi', algorithm='moving_average', window=7, forecast_days=7, compare=False):
    _validate_metric(metric, PREDICTION_METRICS)
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f'不支持的算法: {algorithm}')

    prepared_df = _get_daily_series(city_id, metric, max(240, window * 8))
    predictors = {
        'moving_average': moving_average_predict,
        'weighted_moving_average': weighted_moving_average_predict,
        'linear_regression': linear_regression_predict,
        'holt_winters': holt_winters_predict,
        'arima': arima_predict,
        'lstm': lstm_predict,
    }
    availability = _algorithm_availability()

    result = predictors[algorithm](city_id, metric, window, forecast_days, prepared_df=prepared_df)
    result['requestedAlgorithm'] = algorithm
    result['availability'] = availability

    if compare:
        comparison = []
        for algo in SUPPORTED_ALGORITHMS:
            algo_result = predictors[algo](city_id, metric, window, forecast_days, prepared_df=prepared_df)
            comparison.append({
                'algorithm': algo,
                'selectedAlgorithm': algo_result.get('selectedAlgorithm'),
                'status': algo_result.get('algorithmStatus', 'ok'),
                'available': availability.get(algo, {}).get('available', True),
                'reason': algo_result.get('fallbackReason') or availability.get(algo, {}).get('reason'),
                **algo_result.get('evaluation', {}),
                'usedFallback': algo_result.get('usedFallback', False),
            })
        comparison.sort(key=lambda item: (item.get('mae') is None, item.get('mae') if item.get('mae') is not None else 999999))
        result['comparison'] = comparison
        best = next((item for item in comparison if item.get('mae') is not None and not item.get('usedFallback')), None)
        result['bestAlgorithm'] = best['algorithm'] if best else None
    else:
        result['comparison'] = []
        result['bestAlgorithm'] = None

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
# 2. 多方法异常检测
# ============================================================


def iqr_detect(city_id, metric='aqi', days=90, multiplier=1.5):
    _validate_metric(metric)

    latest = db.session.query(func.max(AirQualityRecord.record_time)).filter(
        AirQualityRecord.city_id == city_id
    ).scalar()
    if not latest:
        return {'method': 'iqr', 'q1': 0, 'q3': 0, 'iqr': 0, 'lower_bound': 0, 'upper_bound': 0, 'anomalies': []}
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
        return {'method': 'iqr', 'q1': 0, 'q3': 0, 'iqr': 0, 'lower_bound': 0, 'upper_bound': 0, 'total_points': len(rows), 'anomaly_count': 0, 'anomalies': []}

    values = np.array([float(r.value) for r in rows])
    dates = [str(r.date) for r in rows]

    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    iqr = q3 - q1
    lower_bound = max(0.0, q1 - multiplier * iqr)
    upper_bound = q3 + multiplier * iqr
    extreme_lower = max(0.0, q1 - 3.0 * iqr)
    extreme_upper = q3 + 3.0 * iqr

    anomalies = []
    for date_str, val in zip(dates, values):
        if val > upper_bound:
            severity = 'severe' if val > extreme_upper else ('moderate' if val > q3 + 2 * iqr else 'mild')
            anomalies.append({'date': date_str, 'value': _safe_round(val), 'type': 'high', 'severity': severity})
        elif val < lower_bound:
            severity = 'severe' if val < extreme_lower else ('moderate' if val < q1 - 2 * iqr else 'mild')
            anomalies.append({'date': date_str, 'value': _safe_round(val), 'type': 'low', 'severity': severity})

    return {
        'method': 'iqr',
        'q1': _safe_round(q1),
        'q3': _safe_round(q3),
        'iqr': _safe_round(iqr),
        'lower_bound': _safe_round(lower_bound),
        'upper_bound': _safe_round(upper_bound),
        'total_points': len(values),
        'anomaly_count': len(anomalies),
        'anomalies': anomalies,
    }



def zscore_detect(city_id, metric='aqi', days=90, threshold=2.5):
    _validate_metric(metric)
    df = _get_daily_series(city_id, metric, days + 30)
    if len(df) < 10:
        return {'method': 'zscore', 'threshold': threshold, 'mean': 0, 'std': 0, 'total_points': len(df), 'anomaly_count': 0, 'anomalies': []}

    values = df['value'].values.astype(float)
    mean = float(np.mean(values))
    std = float(np.std(values) or 0)
    if std == 0:
        return {'method': 'zscore', 'threshold': threshold, 'mean': _safe_round(mean), 'std': 0, 'total_points': len(values), 'anomaly_count': 0, 'anomalies': []}

    anomalies = []
    for idx, val in zip(df.index, values):
        z = (val - mean) / std
        if abs(z) >= threshold:
            anomalies.append({
                'date': idx.strftime('%Y-%m-%d'),
                'value': _safe_round(val),
                'type': 'high' if z > 0 else 'low',
                'severity': 'severe' if abs(z) >= 3.5 else ('moderate' if abs(z) >= 3 else 'mild'),
                'score': _safe_round(z),
            })

    return {
        'method': 'zscore',
        'threshold': threshold,
        'mean': _safe_round(mean),
        'std': _safe_round(std),
        'total_points': len(values),
        'anomaly_count': len(anomalies),
        'anomalies': anomalies,
    }



def mad_detect(city_id, metric='aqi', days=90, threshold=3.5):
    _validate_metric(metric)
    df = _get_daily_series(city_id, metric, days + 30)
    if len(df) < 10:
        return {'method': 'mad', 'threshold': threshold, 'median': 0, 'mad': 0, 'total_points': len(df), 'anomaly_count': 0, 'anomalies': []}

    values = df['value'].values.astype(float)
    median = float(np.median(values))
    abs_dev = np.abs(values - median)
    mad = float(np.median(abs_dev) or 0)
    if mad == 0:
        return {'method': 'mad', 'threshold': threshold, 'median': _safe_round(median), 'mad': 0, 'total_points': len(values), 'anomaly_count': 0, 'anomalies': []}

    modified_z = 0.6745 * (values - median) / mad
    anomalies = []
    for idx, val, score in zip(df.index, values, modified_z):
        if abs(score) >= threshold:
            anomalies.append({
                'date': idx.strftime('%Y-%m-%d'),
                'value': _safe_round(val),
                'type': 'high' if score > 0 else 'low',
                'severity': 'severe' if abs(score) >= 5 else ('moderate' if abs(score) >= 4.2 else 'mild'),
                'score': _safe_round(score),
            })

    return {
        'method': 'mad',
        'threshold': threshold,
        'median': _safe_round(median),
        'mad': _safe_round(mad),
        'total_points': len(values),
        'anomaly_count': len(anomalies),
        'anomalies': anomalies,
    }



def run_anomaly_pipeline(city_id, metric='aqi', days=90, method='iqr', compare=False, multiplier=1.5):
    if method not in SUPPORTED_ANOMALY_METHODS:
        raise ValueError(f'不支持的异常检测方法: {method}')

    runners = {
        'iqr': lambda: iqr_detect(city_id, metric, days, multiplier),
        'zscore': lambda: zscore_detect(city_id, metric, days),
        'mad': lambda: mad_detect(city_id, metric, days),
    }
    result = runners[method]()
    result['selectedMethod'] = method
    if compare:
        result['comparison'] = [
            {
                'method': name,
                'anomalyCount': runners[name]().get('anomaly_count', 0),
            }
            for name in SUPPORTED_ANOMALY_METHODS
        ]
    else:
        result['comparison'] = []
    return result


# ============================================================
# 3. 风险评分
# ============================================================


def _risk_level(score):
    if score >= 80:
        return 'severe'
    if score >= 60:
        return 'high'
    if score >= 35:
        return 'medium'
    return 'low'



def calculate_risk_score(city_id, forecast_days=5):
    base_df = _get_daily_series(city_id, 'aqi', 30)
    if base_df.empty:
        return {
            'score': 0,
            'level': 'low',
            'summary': '暂无可用数据',
            'drivers': [],
            'futureRisk': [],
            'metricPredictions': {},
            'components': {'pollution': 0, 'diffusion': 0, 'anomaly': 0, 'forecast': 0},
            'basis': [],
        }

    latest_record = AirQualityRecord.query.filter_by(city_id=city_id).order_by(AirQualityRecord.record_time.desc()).first()
    if not latest_record:
        return {
            'score': 0,
            'level': 'low',
            'summary': '暂无可用数据',
            'drivers': [],
            'futureRisk': [],
            'metricPredictions': {},
            'components': {'pollution': 0, 'diffusion': 0, 'anomaly': 0, 'forecast': 0},
            'basis': [],
        }

    def ratio_score(value, limit, weight):
        if value is None or limit <= 0:
            return 0.0
        ratio = float(value) / limit
        return min(100.0, max(0.0, ratio * 100.0)) * weight

    pollutant_limits = {
        'aqi': 100,
        'pm25': 75,
        'pm10': 150,
        'o3': 160,
        'no2': 80,
        'so2': 60,
    }
    pollutant_weights = {
        'aqi': 0.28,
        'pm25': 0.20,
        'pm10': 0.14,
        'o3': 0.12,
        'no2': 0.08,
        'so2': 0.06,
    }

    pollution_contrib = {}
    for metric, weight in pollutant_weights.items():
        pollution_contrib[metric] = ratio_score(getattr(latest_record, metric), pollutant_limits[metric], weight)
    pollution_score = min(55.0, sum(pollution_contrib.values()))

    humidity = float(latest_record.humidity or 0)
    wind_speed = float(latest_record.wind_speed or 0)
    rainfall = float(latest_record.rainfall or 0)
    temperature = float(latest_record.temperature or 0)
    diffusion_score = 0.0
    if humidity >= 80:
        diffusion_score += 8
    elif humidity >= 65:
        diffusion_score += 4
    if wind_speed <= 1.5:
        diffusion_score += 10
    elif wind_speed <= 3:
        diffusion_score += 5
    if rainfall <= 0.2:
        diffusion_score += 4
    if temperature >= 32 or temperature <= 0:
        diffusion_score += 3
    diffusion_score = min(25.0, diffusion_score)

    anomaly_methods = {
        'iqr': iqr_detect(city_id, 'aqi', 60).get('anomaly_count', 0),
        'zscore': zscore_detect(city_id, 'aqi', 60).get('anomaly_count', 0),
        'mad': mad_detect(city_id, 'aqi', 60).get('anomaly_count', 0),
    }
    anomaly_score = min(10.0, anomaly_methods['iqr'] * 1.5 + anomaly_methods['zscore'] * 1.2 + anomaly_methods['mad'] * 1.2)

    forecast_algorithm = 'holt_winters'
    metric_predictions = {}
    future_risk = []
    future_component = 0.0
    for metric in PREDICTION_METRICS:
        pred = run_prediction_pipeline(city_id, metric=metric, algorithm=forecast_algorithm, forecast_days=forecast_days, compare=False)
        metric_predictions[metric] = pred.get('predictions', [])

    for idx in range(forecast_days):
        aqi_pred = metric_predictions['aqi'][idx]['predicted'] if idx < len(metric_predictions['aqi']) else float(latest_record.aqi or 0)
        pm25_pred = metric_predictions['pm25'][idx]['predicted'] if idx < len(metric_predictions['pm25']) else float(latest_record.pm25 or 0)
        pm10_pred = metric_predictions['pm10'][idx]['predicted'] if idx < len(metric_predictions['pm10']) else float(latest_record.pm10 or 0)
        o3_pred = metric_predictions['o3'][idx]['predicted'] if idx < len(metric_predictions['o3']) else float(latest_record.o3 or 0)
        day_score = min(100.0, (
            (aqi_pred / 100) * 34 +
            (pm25_pred / 75) * 28 +
            (pm10_pred / 150) * 20 +
            (o3_pred / 160) * 18
        ))
        date = metric_predictions['aqi'][idx]['date'] if idx < len(metric_predictions['aqi']) else None
        level = _risk_level(day_score)
        future_risk.append({'date': date, 'score': _safe_round(day_score), 'level': level})
        future_component = max(future_component, day_score * 0.1)

    forecast_score = min(10.0, future_component)
    total_score = min(100.0, _safe_round(pollution_score + diffusion_score + anomaly_score + forecast_score))
    level = _risk_level(total_score)

    drivers = []
    metric_labels = {
        'aqi': 'AQI',
        'pm25': 'PM2.5',
        'pm10': 'PM10',
        'o3': 'O₃',
        'no2': 'NO₂',
        'so2': 'SO₂',
    }
    for metric, contrib in pollution_contrib.items():
        drivers.append({'factor': metric, 'label': metric_labels.get(metric, metric.upper()), 'value': _safe_round(getattr(latest_record, metric)), 'contribution': _safe_round(contrib)})
    drivers.extend([
        {'factor': 'humidity', 'label': '湿度', 'value': _safe_round(humidity), 'contribution': _safe_round(8 if humidity >= 80 else (4 if humidity >= 65 else 0))},
        {'factor': 'wind_speed', 'label': '风速', 'value': _safe_round(wind_speed), 'contribution': _safe_round(10 if wind_speed <= 1.5 else (5 if wind_speed <= 3 else 0))},
        {'factor': 'future_trend', 'label': '未来趋势', 'value': future_risk[0]['score'] if future_risk else 0, 'contribution': _safe_round(forecast_score)},
    ])
    drivers.sort(key=lambda item: item.get('contribution') or 0, reverse=True)

    basis = [
        '污染暴露分：依据 AQI、PM2.5、PM10、O₃、NO₂、SO₂ 与国标限值的占比加权计算',
        '扩散条件分：依据湿度、风速、降雨、温度判断污染扩散难度',
        '异常波动分：融合 IQR、Z-score、MAD 三种异常检测结果',
        '未来趋势分：依据未来 5 天预测污染水平上限补充风险',
    ]

    summary = (
        f'当前综合风险为{level}，总分 {total_score}。'
        f'污染暴露贡献 { _safe_round(pollution_score) }，扩散条件贡献 { _safe_round(diffusion_score) }，'
        f'异常波动贡献 { _safe_round(anomaly_score) }，未来趋势贡献 { _safe_round(forecast_score) }。'
    )
    return {
        'score': total_score,
        'level': level,
        'summary': summary,
        'drivers': drivers[:6],
        'futureRisk': future_risk,
        'metricPredictions': metric_predictions,
        'components': {
            'pollution': _safe_round(pollution_score),
            'diffusion': _safe_round(diffusion_score),
            'anomaly': _safe_round(anomaly_score),
            'forecast': _safe_round(forecast_score),
        },
        'basis': basis,
        'forecastAlgorithm': forecast_algorithm,
        'recordDate': latest_record.record_time.strftime('%Y-%m-%d'),
        'dataSource': 'local_db_daily_avg',
        'anomalySignals': anomaly_methods,
    }



def save_anomalies(city_id, metric, detect_result):
    """将异常检测结果持久化到 anomaly_events 表"""
    for a in detect_result['anomalies']:
        event = AnomalyEvent(
            city_id=city_id,
            metric_name=metric,
            record_time=datetime.strptime(a['date'], '%Y-%m-%d'),
            actual_value=a['value'],
            q1_value=detect_result.get('q1', 0),
            q3_value=detect_result.get('q3', 0),
            iqr_value=detect_result.get('iqr', 0),
            lower_bound=detect_result.get('lower_bound', 0),
            upper_bound=detect_result.get('upper_bound', 0),
            anomaly_type=a['type'],
            severity=a['severity'],
        )
        db.session.add(event)
    db.session.commit()


# ============================================================
# 4. 批量运行入口（供 CLI / 定时任务调用）
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
