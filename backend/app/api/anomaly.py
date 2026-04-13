"""异常检测与风险评分 API"""
from flask import request
from app.api import api_bp
from app.services.algorithm import run_anomaly_pipeline, save_anomalies, calculate_risk_score, SUPPORTED_ANOMALY_METHODS
from app.models import AnomalyEvent
from app.utils.response import success, error
from app import db


@api_bp.route('/anomaly/detect', methods=['POST'])
def run_anomaly_detect():
    """
    对指定城市执行异常检测（实时计算 + IQR结果可持久化）
    Body JSON: { cityId, metric?, days?, method?, compare?, multiplier? }
    """
    data = request.get_json(silent=True) or {}
    city_id = data.get('cityId')
    if not city_id:
        return error('缺少 cityId')

    metric = data.get('metric', 'aqi')
    days = data.get('days', 90)
    method = data.get('method', 'iqr')
    compare = bool(data.get('compare', False))
    multiplier = data.get('multiplier', 1.5)

    try:
        result = run_anomaly_pipeline(city_id, metric, days, method, compare, multiplier)
    except ValueError as e:
        return error(str(e))

    if method == 'iqr':
        AnomalyEvent.query.filter_by(city_id=city_id, metric_name=metric).delete()
        db.session.commit()
        if result['anomalies']:
            save_anomalies(city_id, metric, result)

    result['supportedMethods'] = SUPPORTED_ANOMALY_METHODS
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

    # 确认异常后，自动调用 AI 生成归因分析
    if new_status == 'confirmed' and not event.ai_analysis:
        try:
            from app.services.ai_service import chat_with_qwen
            from app.models import City
            city = City.query.get(event.city_id)
            city_name = city.name if city else '未知城市'

            metric_names = {
                'aqi': 'AQI（空气质量指数）',
                'pm25': 'PM2.5（细颗粒物）',
                'pm10': 'PM10（可吸入颗粒物）',
                'o3': 'O3（臭氧）',
                'no2': 'NO2（二氧化氮）',
                'so2': 'SO2（二氧化硫）',
                'co': 'CO（一氧化碳）',
            }
            metric_label = metric_names.get(event.metric_name, event.metric_name)
            direction = '异常偏高' if event.anomaly_type == 'high' else '异常偏低'
            severity_text = {'severe': '严重', 'moderate': '中度', 'mild': '轻度'}.get(event.severity, event.severity)

            prompt = (
                f"以下是一条已确认的空气质量异常事件，请分析可能的原因并给出应对建议：\n\n"
                f"- 城市：{city_name}\n"
                f"- 指标：{metric_label}\n"
                f"- 日期：{event.record_time.strftime('%Y-%m-%d')}\n"
                f"- 实际值：{float(event.actual_value)}\n"
                f"- 正常范围：{float(event.lower_bound)} ~ {float(event.upper_bound)}\n"
                f"- 异常方向：{direction}\n"
                f"- 严重程度：{severity_text}\n\n"
                f"请从以下角度分析：\n"
                f"1. 可能的污染来源或气象原因（2-3条）\n"
                f"2. 对居民健康的影响\n"
                f"3. 建议采取的应对措施\n"
                f"请控制在200字以内，简洁专业。"
            )

            result = chat_with_qwen(prompt)
            event.ai_analysis = result.get('content', '')
            db.session.commit()
        except Exception as e:
            print(f'[AI Analysis] 异常归因分析失败: {e}')

    return success(event.to_dict())
