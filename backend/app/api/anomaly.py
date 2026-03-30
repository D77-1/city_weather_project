"""异常检测与风险评分 API"""
from flask import request
from app.api import api_bp
from app.services.algorithm import iqr_detect, save_anomalies, calculate_risk_score
from app.models import AnomalyEvent
from app.utils.response import success, error
from app import db


@api_bp.route('/anomaly/detect', methods=['POST'])
def run_anomaly_detect():
    """
    对指定城市执行 IQR 异常检测（实时计算 + 持久化结果）
    Body JSON: { cityId, metric?, days?, multiplier? }
    """
    data = request.get_json(silent=True) or {}
    city_id = data.get('cityId')
    if not city_id:
        return error('缺少 cityId')

    metric = data.get('metric', 'aqi')
    days = data.get('days', 90)
    multiplier = data.get('multiplier', 1.5)

    try:
        result = iqr_detect(city_id, metric, days, multiplier)
    except ValueError as e:
        return error(str(e))

    AnomalyEvent.query.filter_by(city_id=city_id, metric_name=metric).delete()
    db.session.commit()

    if result['anomalies']:
        save_anomalies(city_id, metric, result)

    return success(result)


@api_bp.route('/risk/assess', methods=['POST'])
def assess_risk():
    """
    计算指定城市综合风险评分
    Body JSON: { cityId, forecastDays? }
    """
    data = request.get_json(silent=True) or {}
    city_id = data.get('cityId')
    if not city_id:
        return error('缺少 cityId')

    forecast_days = data.get('forecastDays', 5)
    result = calculate_risk_score(city_id, forecast_days)
    return success(result)


@api_bp.route('/anomaly/list', methods=['GET'])
def get_anomaly_list():
    """
    获取异常事件列表
    参数: city_id(可选), metric(可选), severity(可选), status(可选), limit(默认50)
    """
    query = AnomalyEvent.query

    city_id = request.args.get('city_id', type=int)
    if city_id:
        query = query.filter(AnomalyEvent.city_id == city_id)

    metric = request.args.get('metric')
    if metric:
        query = query.filter(AnomalyEvent.metric_name == metric)

    severity = request.args.get('severity')
    if severity:
        query = query.filter(AnomalyEvent.severity == severity)

    status = request.args.get('status')
    if status:
        query = query.filter(AnomalyEvent.status == status)

    limit = min(request.args.get('limit', 50, type=int), 200)
    events = query.order_by(AnomalyEvent.record_time.desc()).limit(limit).all()
    return success([e.to_dict() for e in events])


@api_bp.route('/anomaly/<int:event_id>/status', methods=['PUT'])
def update_anomaly_status(event_id):
    """更新异常事件状态 Body: { status: 'confirmed'|'dismissed' }"""
    event = AnomalyEvent.query.get(event_id)
    if not event:
        return error('异常事件不存在', 404)

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ('confirmed', 'dismissed'):
        return error('status 必须为 confirmed 或 dismissed')

    event.status = new_status
    db.session.commit()
    return success(event.to_dict())
