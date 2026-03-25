from app import db
from datetime import datetime


class User(db.Model):
    """用户信息"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50))
    avatar_url = db.Column(db.String(500))
    role = db.Column(db.Enum('admin', 'user'), default='user')
    openid = db.Column(db.String(100), unique=True, comment='微信OpenID')
    phone = db.Column(db.String(20))
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    ai_logs = db.relationship('AIInteractionLog', backref='user', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'avatarUrl': self.avatar_url,
            'role': self.role,
            'phone': self.phone,
            'lastLoginAt': self.last_login_at.strftime('%Y-%m-%d %H:%M:%S') if self.last_login_at else None,
        }
