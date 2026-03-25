"""AI 建议接口"""
import uuid
from flask import request
from app.api import api_bp
from app import db
from app.services.ai_service import chat_with_qwen
from app.models import AIInteractionLog
from app.utils.response import success, error


@api_bp.route('/ai/advice', methods=['POST'])
def get_ai_advice():
    """
    获取 AI 分析建议
    Body JSON:
    {
        "message": "用户问题",
        "sessionId": "可选,会话ID",
        "cityId": 可选,
        "context": { 可选, cityName, current, prediction, anomalies }
    }
    """
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return error('消息不能为空')

    session_id = data.get('sessionId', str(uuid.uuid4()))
    city_id = data.get('cityId')
    context_data = data.get('context')

    # 调用通义千问
    result = chat_with_qwen(message, context_data)

    # 记录到日志表
    log = AIInteractionLog(
        city_id=city_id,
        session_id=session_id,
        user_message=message,
        ai_response=result['content'],
        context_data=context_data,
        tokens_used=result['tokens'],
        response_time_ms=result['elapsed_ms'],
        source='web',
    )
    db.session.add(log)
    db.session.commit()

    return success({
        'content': result['content'],
        'sessionId': session_id,
        'tokensUsed': result['tokens'],
        'responseTimeMs': result['elapsed_ms'],
    })


@api_bp.route('/ai/history', methods=['GET'])
def get_ai_history():
    """获取 AI 对话历史 参数: session_id"""
    session_id = request.args.get('session_id')
    if not session_id:
        return error('缺少 session_id')

    logs = AIInteractionLog.query.filter_by(session_id=session_id) \
        .order_by(AIInteractionLog.created_at).all()

    return success([l.to_dict() for l in logs])
