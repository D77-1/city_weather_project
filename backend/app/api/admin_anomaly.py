"""管理员模块: 异常事件批量审核"""
from datetime import datetime

from flask import request, g

from app import db
from app.api import api_bp
from app.models import AnomalyEvent
from app.utils.auth import admin_required
from app.utils.response import success, error


VALID_ACTIONS = {'confirmed', 'dismissed', 'pending'}


@api_bp.route('/admin/anomalies/batch-review', methods=['POST'])
@admin_required
def batch_review():
    """
    批量更新异常事件状态
    Body: { ids: [int], action: 'confirmed' | 'dismissed' | 'pending' }
    """
    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []
    action = data.get('action')

    if not isinstance(ids, list) or not ids:
        return error('ids 不能为空')
    if action not in VALID_ACTIONS:
        return error(f'action 必须是 {VALID_ACTIONS} 之一')

    events = AnomalyEvent.query.filter(AnomalyEvent.id.in_(ids)).all()
    if not events:
        return error('没有匹配的异常事件', 404)

    uid = g.current_user['uid']
    now = datetime.now()
    for e in events:
        e.status = action
        e.reviewed_by = uid
        e.reviewed_at = now

    db.session.commit()
    return success({'updated': len(events), 'action': action})
