"""异常检测与风险评分 API"""
from datetime import datetime

from flask import request, g
from app.api import api_bp
from app.services.algorithm import run_anomaly_pipeline, save_anomalies, calculate_risk_score, SUPPORTED_ANOMALY_METHODS
from app.models import AnomalyEvent
from app.utils.auth import admin_required
from app.utils.response import success, error
from app import db


@api_bp.route('/anomaly/detect', methods=['POST'])
@admin_required
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
        # 保留 dismissed（误报）记录，仅重建非误报事件，确保反馈闭环不丢失
        AnomalyEvent.query.filter(
            AnomalyEvent.city_id == city_id,
            AnomalyEvent.metric_name == metric,
            AnomalyEvent.status != 'dismissed',
        ).delete(synchronize_session=False)
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


def _generate_ai_attribution(event):
    """对单条异常事件调用大模型生成归因分析文本"""
    from app.services.ai_service import chat_with_qwen
    from app.models import City, AirQualityRecord

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

    # 取当日气象上下文，供大模型做更具体的归因
    weather_line = ''
    record = AirQualityRecord.query.filter_by(city_id=event.city_id).filter(
        AirQualityRecord.record_time >= event.record_time.replace(hour=0, minute=0, second=0),
    ).order_by(AirQualityRecord.record_time).first()
    if record is not None:
        parts = []
        if record.temperature is not None:
            parts.append(f'气温 {float(record.temperature):.1f}℃')
        if record.humidity is not None:
            parts.append(f'湿度 {float(record.humidity):.0f}%')
        if record.wind_speed is not None:
            parts.append(f'风速 {float(record.wind_speed):.1f} m/s')
        if record.rainfall is not None:
            parts.append(f'降雨 {float(record.rainfall):.1f} mm')
        if parts:
            weather_line = f"- 当日气象：{'、'.join(parts)}\n"

    deviation = float(event.actual_value) - (float(event.upper_bound) if event.anomaly_type == 'high' else float(event.lower_bound))

    prompt = (
        f"你是大气环境分析助理，请对下列异常事件做归因分析，不要使用模板化措辞：\n\n"
        f"- 城市：{city_name}\n"
        f"- 指标：{metric_label}\n"
        f"- 日期：{event.record_time.strftime('%Y-%m-%d')}\n"
        f"- 实际值：{float(event.actual_value)}（偏离阈值 {deviation:+.1f}）\n"
        f"- IQR 正常范围：{float(event.lower_bound)} ~ {float(event.upper_bound)}\n"
        f"- 异常方向：{direction}\n"
        f"- 严重程度：{severity_text}\n"
        f"{weather_line}\n"
        f"请严格按三段输出，每段一行标题并以中文冒号结尾，正文紧跟其后：\n"
        f"1. 可能成因：结合污染物化学特性、当日气象、典型排放源，给出 2~3 条具体推测\n"
        f"2. 健康影响：针对该污染物与异常幅度，说明易感人群的短期风险\n"
        f"3. 处置建议：给出 2 条可操作的公众防护或监管动作\n"
        f"全文不超过 220 字。"
    )
    result = chat_with_qwen(prompt)
    return result.get('content', '')


@api_bp.route('/anomaly/<int:event_id>/analyze', methods=['POST'])
@admin_required
def analyze_anomaly(event_id):
    """
    对单条异常事件生成 AI 归因分析。
    Body JSON: { force?: bool }  force=true 时强制重新生成
    """
    event = AnomalyEvent.query.get(event_id)
    if not event:
        return error('异常事件不存在', 404)

    data = request.get_json(silent=True) or {}
    force = bool(data.get('force', False))

    if event.ai_analysis and not force:
        # 已有分析直接返回，避免反复消耗 token
        return success(event.to_dict())

    try:
        content = _generate_ai_attribution(event)
    except Exception as e:
        return error(f'归因分析生成失败：{e}', 500)

    event.ai_analysis = content
    event.status = 'confirmed'  # 沿用 enum；语义：已归因
    db.session.commit()
    return success(event.to_dict())


@api_bp.route('/anomaly/<int:event_id>/status', methods=['PUT'])
@admin_required
def update_anomaly_status(event_id):
    """
    更新异常事件状态（仅用于标记误报）。
    Body: { status: 'dismissed' | 'pending' }
    说明：status=confirmed 由 /anomaly/<id>/analyze 接口自动设置，此处不再接收。
    标记为 dismissed 的点会被下一次 IQR 检测剔除，形成反馈闭环。
    """
    event = AnomalyEvent.query.get(event_id)
    if not event:
        return error('异常事件不存在', 404)

    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    if new_status not in ('dismissed', 'pending'):
        return error('status 必须为 dismissed 或 pending')

    event.status = new_status
    event.reviewed_by = g.current_user['uid']
    event.reviewed_at = datetime.now()
    db.session.commit()
    return success(event.to_dict())
