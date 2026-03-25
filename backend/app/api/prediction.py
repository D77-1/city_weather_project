"""预测结果 API"""
from flask import request
from app.api import api_bp
from app.services.algorithm import moving_average_predict
from app.models import PredictionResult
from app.utils.response import success, error


@api_bp.route('/prediction/run', methods=['POST'])
def run_prediction():
    """
    对指定城市执行移动平均预测（实时计算，不持久化）
    Body JSON: { cityId, metric?, window?, forecastDays? }
    """
    data = request.get_json(silent=True) or {}
    city_id = data.get('cityId')
    if not city_id:
        return error('缺少 cityId')

    metric = data.get('metric', 'aqi')
    window = data.get('window', 7)
    forecast_days = data.get('forecastDays', 7)

    try:
        result = moving_average_predict(city_id, metric, window, forecast_days)
    except ValueError as e:
        return error(str(e))

    return success(result)


@api_bp.route('/prediction/history', methods=['GET'])
def get_prediction_history():
    """
    获取已持久化的预测记录
    参数: city_id, metric(默认aqi), limit(默认30)
    """
    city_id = request.args.get('city_id', type=int)
    if not city_id:
        return error('缺少 city_id')

    metric = request.args.get('metric', 'aqi')
    limit = min(request.args.get('limit', 30, type=int), 100)

    records = PredictionResult.query.filter_by(
        city_id=city_id, metric_name=metric,
    ).order_by(PredictionResult.prediction_date.desc()).limit(limit).all()

    return success([r.to_dict() for r in records])
