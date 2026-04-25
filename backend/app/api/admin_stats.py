"""管理员模块: 仪表盘指标"""
from datetime import datetime, timedelta

from sqlalchemy import func

from app import db
from app.api import api_bp
from app.models import (
    AirQualityRecord,
    AnomalyEvent,
    AIInteractionLog,
    City,
    MonitoringStation,
    User,
)
from app.utils.auth import admin_required
from app.utils.response import success


@api_bp.route('/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    """
    返回管理员仪表盘所需的核心指标
    """
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())

    # 记录总数 / 城市 / 站点
    total_records = db.session.query(func.count(AirQualityRecord.id)).scalar() or 0
    active_cities = db.session.query(func.count(City.id)).scalar() or 0
    active_stations = (
        db.session.query(func.count(MonitoringStation.id))
        .filter(MonitoringStation.status == 'active')
        .scalar()
        or 0
    )

    # 异常
    pending_anomalies = (
        db.session.query(func.count(AnomalyEvent.id))
        .filter(AnomalyEvent.status == 'pending')
        .scalar()
        or 0
    )
    confirmed_anomalies = (
        db.session.query(func.count(AnomalyEvent.id))
        .filter(AnomalyEvent.status == 'confirmed')
        .scalar()
        or 0
    )
    dismissed_anomalies = (
        db.session.query(func.count(AnomalyEvent.id))
        .filter(AnomalyEvent.status == 'dismissed')
        .scalar()
        or 0
    )

    # AI 调用
    ai_total = db.session.query(func.count(AIInteractionLog.id)).scalar() or 0
    ai_today = (
        db.session.query(func.count(AIInteractionLog.id))
        .filter(AIInteractionLog.created_at >= today_start)
        .scalar()
        or 0
    )
    ai_tokens_total = db.session.query(func.coalesce(func.sum(AIInteractionLog.tokens_used), 0)).scalar() or 0

    # 用户 / 最近登录
    total_users = db.session.query(func.count(User.id)).scalar() or 0
    admin_users = db.session.query(func.count(User.id)).filter(User.role == 'admin').scalar() or 0

    recent_logins = (
        User.query.filter(User.last_login_at.isnot(None))
        .order_by(User.last_login_at.desc())
        .limit(5)
        .all()
    )
    recent_logins_payload = [
        {
            'id': u.id,
            'username': u.username,
            'nickname': u.nickname,
            'role': u.role,
            'lastLoginAt': u.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if u.last_login_at else None,
        }
        for u in recent_logins
    ]

    # 最新一条空气质量记录时间
    latest_record_time = db.session.query(func.max(AirQualityRecord.record_time)).scalar()

    # 最近 7 天异常趋势
    seven_days_ago = today_start - timedelta(days=6)
    anomaly_trend_rows = (
        db.session.query(
            func.date(AnomalyEvent.record_time).label('day'),
            func.count(AnomalyEvent.id).label('cnt'),
        )
        .filter(AnomalyEvent.record_time >= seven_days_ago)
        .group_by('day')
        .order_by('day')
        .all()
    )
    anomaly_trend = [
        {'date': str(r.day), 'count': int(r.cnt)} for r in anomaly_trend_rows
    ]

    return success({
        'totalRecords': int(total_records),
        'activeCities': int(active_cities),
        'activeStations': int(active_stations),
        'anomalies': {
            'pending': int(pending_anomalies),
            'confirmed': int(confirmed_anomalies),
            'dismissed': int(dismissed_anomalies),
            'total': int(pending_anomalies + confirmed_anomalies + dismissed_anomalies),
        },
        'aiCalls': {
            'total': int(ai_total),
            'today': int(ai_today),
            'tokensTotal': int(ai_tokens_total),
        },
        'users': {
            'total': int(total_users),
            'admin': int(admin_users),
        },
        'recentLogins': recent_logins_payload,
        'latestRecordTime': latest_record_time.strftime('%Y-%m-%d %H:%M:%S') if latest_record_time else None,
        'anomalyTrend7d': anomaly_trend,
    })
