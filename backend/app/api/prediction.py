"""预测结果 API"""
from flask import request
from app.api import api_bp
from app.services.algorithm import run_prediction_pipeline, SUPPORTED_ALGORITHMS
from app.models import PredictionResult
from app.utils.response import success, error


@api_bp.route('/prediction/run', methods=['POST'])
def run_prediction():
    """
    对指定城市执行多模型预测（实时计算，不持久化）
    Body JSON: { cityId, metric?, window?, forecastDays?, algorithm?, compare? }
    """
    data = request.get_json(silent=True) or {}
    city_id = data.get('cityId')
    if not city_id:
        return error('缺少 cityId')

    metric = data.get('metric', 'aqi')
    window = data.get('window', 7)
    forecast_days = data.get('forecastDays', 5)
    algorithm = data.get('algorithm', 'moving_average')
    compare = bool(data.get('compare', False))

    try:
        result = run_prediction_pipeline(city_id, metric, algorithm, window, forecast_days, compare)
    except ValueError as e:
        return error(str(e))

    result['supportedAlgorithms'] = SUPPORTED_ALGORITHMS
    return success(result)


@api_bp.route('/prediction/history', methods=['GET'])
def get_prediction_history():
    """
    获取已持久化的预测记录
    参数: city_id, metric(默认aqi), algorithm_type(可选), limit(默认30)
    """
    city_id = request.args.get('city_id', type=int)
    if not city_id:
        return error('缺少 city_id')

    metric = request.args.get('metric', 'aqi')
    algorithm_type = request.args.get('algorithm_type')
    limit = min(request.args.get('limit', 30, type=int), 100)

    query = PredictionResult.query.filter_by(city_id=city_id, metric_name=metric)
    if algorithm_type:
        query = query.filter_by(algorithm_type=algorithm_type)

    records = query.order_by(PredictionResult.prediction_date.desc()).limit(limit).all()
    return success([r.to_dict() for r in records])
