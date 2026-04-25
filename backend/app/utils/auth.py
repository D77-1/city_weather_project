"""JWT 鉴权 + 密码哈希工具"""
from functools import wraps
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from flask import request, current_app, g

from app.utils.response import error


def hash_password(plain: str) -> str:
    """bcrypt 加盐哈希，返回可直接入库的字符串"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def generate_token(user) -> str:
    """根据 User 对象生成 JWT"""
    cfg = current_app.config
    payload = {
        'uid': user.id,
        'username': user.username,
        'role': user.role,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=cfg['JWT_EXPIRE_HOURS']),
    }
    return jwt.encode(payload, cfg['JWT_SECRET_KEY'], algorithm=cfg['JWT_ALGORITHM'])


def decode_token(token: str):
    """解码 token，异常时返回 None"""
    if not token:
        return None
    cfg = current_app.config
    try:
        return jwt.decode(token, cfg['JWT_SECRET_KEY'], algorithms=[cfg['JWT_ALGORITHM']])
    except jwt.ExpiredSignatureError:
        return {'_error': 'expired'}
    except jwt.InvalidTokenError:
        return {'_error': 'invalid'}


def _get_token_from_header():
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header[7:].strip()
    return None


def login_required(func):
    """仅校验登录态，不校验角色"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = _get_token_from_header()
        payload = decode_token(token)
        if not payload:
            return error('未登录或令牌无效', 401)
        if payload.get('_error') == 'expired':
            return error('登录已过期，请重新登录', 401)
        if payload.get('_error') == 'invalid':
            return error('令牌无效', 401)
        g.current_user = payload
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    """要求 admin 角色"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = _get_token_from_header()
        payload = decode_token(token)
        if not payload or payload.get('_error'):
            reason = payload.get('_error') if payload else 'missing'
            msg = {'expired': '登录已过期，请重新登录', 'invalid': '令牌无效'}.get(reason, '未登录')
            return error(msg, 401)
        if payload.get('role') != 'admin':
            return error('需要管理员权限', 403)
        g.current_user = payload
        return func(*args, **kwargs)
    return wrapper
