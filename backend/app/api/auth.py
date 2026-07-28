"""登录与当前用户信息"""
from datetime import datetime

from flask import request, g

from app import db
from app.api import api_bp
from app.models import User
from app.utils.auth import verify_password, generate_token, admin_required
from app.utils.response import success, error


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户名密码登录，返回 JWT"""
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return error('用户名和密码不能为空')

    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return error('用户名或密码错误', 401)

    # 当前仅允许 admin 登录（普通 user 角色不落地）
    if user.role != 'admin':
        return error('账号无后台访问权限', 403)

    user.last_login_at = datetime.now()
    db.session.commit()

    token = generate_token(user)
    return success({'token': token, 'user': user.to_dict()})


@api_bp.route('/auth/me', methods=['GET'])
@admin_required
def current_user_info():
    """前端刷新页面时用来恢复登录态"""
    uid = g.current_user['uid']
    user = User.query.get(uid)
    if not user:
        return error('用户不存在', 404)
    return success(user.to_dict())
