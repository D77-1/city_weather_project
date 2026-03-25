from app import db
from datetime import datetime


class AIInteractionLog(db.Model):
    """AI 对话日志"""
    __tablename__ = 'ai_interaction_logs'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id', ondelete='SET NULL'), nullable=True)
    session_id = db.Column(db.String(64), nullable=False, comment='会话UUID')
    user_message = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text)
    context_data = db.Column(db.JSON, comment='传入AI的上下文数据')
    model_name = db.Column(db.String(50), default='qwen-turbo')
    tokens_used = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)
    source = db.Column(db.Enum('web', 'miniapp'), default='web')
    created_at = db.Column(db.DateTime, default=datetime.now)

    city = db.relationship('City', backref=db.backref('ai_logs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'cityId': self.city_id,
            'sessionId': self.session_id,
            'userMessage': self.user_message,
            'aiResponse': self.ai_response,
            'modelName': self.model_name,
            'tokensUsed': self.tokens_used,
            'responseTimeMs': self.response_time_ms,
            'source': self.source,
            'createdAt': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
