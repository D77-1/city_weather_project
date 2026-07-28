"""管理员模块: AI 对话日志审计"""
from datetime import datetime

from flask import request

from app.api import api_bp
from app.models import AIInteractionLog, City, User
from app.utils.auth import admin_required
from app.utils.response import success, error


def _parse_datetime(value: str):
    if not value:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


@api_bp.route('/admin/ai-logs', methods=['GET'])
@admin_required
def list_ai_logs():
    """
    分页列表 + 多条件筛选
    列表不返 context_data（避免大字段污染）
    """
    page = max(request.args.get('page', 1, type=int), 1)
    size = min(max(request.args.get('size', 20, type=int), 1), 100)
    session_id = request.args.get('sessionId')
    source = request.args.get('source')
    start = _parse_datetime(request.args.get('startTime'))
    end = _parse_datetime(request.args.get('endTime'))
    city_id = request.args.get('cityId', type=int)
    user_id = request.args.get('userId', type=int)

    query = AIInteractionLog.query
    if session_id:
        query = query.filter(AIInteractionLog.session_id == session_id)
    if source in ('web', 'miniapp'):
        query = query.filter(AIInteractionLog.source == source)
    if start:
        query = query.filter(AIInteractionLog.created_at >= start)
    if end:
        query = query.filter(AIInteractionLog.created_at <= end)
    if city_id:
        query = query.filter(AIInteractionLog.city_id == city_id)
    if user_id:
        query = query.filter(AIInteractionLog.user_id == user_id)

    total = query.count()
    logs = (
        query.order_by(AIInteractionLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    # 预拉相关 city/user 名字，避免 N+1
    city_ids = {l.city_id for l in logs if l.city_id}
    user_ids = {l.user_id for l in logs if l.user_id}
    city_map = {c.id: c.name for c in City.query.filter(City.id.in_(city_ids)).all()} if city_ids else {}
    user_map = {u.id: (u.nickname or u.username) for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    items = []
    for l in logs:
        preview = (l.user_message or '').strip()
        if len(preview) > 80:
            preview = preview[:80] + '…'
        items.append({
            'id': l.id,
            'sessionId': l.session_id,
            'source': l.source,
            'modelName': l.model_name,
            'tokensUsed': l.tokens_used,
            'responseTimeMs': l.response_time_ms,
            'userMessagePreview': preview,
            'cityId': l.city_id,
            'cityName': city_map.get(l.city_id),
            'userId': l.user_id,
            'userName': user_map.get(l.user_id),
            'createdAt': l.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })

    return success({
        'total': total,
        'page': page,
        'size': size,
        'items': items,
    })


@api_bp.route('/admin/ai-logs/<int:log_id>', methods=['GET'])
@admin_required
def get_ai_log_detail(log_id):
    log = AIInteractionLog.query.get(log_id)
    if not log:
        return error('日志不存在', 404)

    detail = log.to_dict()
    detail['contextData'] = log.context_data  # 详情才返
    return success(detail)
