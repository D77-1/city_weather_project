"""管理员模块: 用户管理 CRUD"""
from flask import request, g
from sqlalchemy import or_

from app import db
from app.api import api_bp
from app.models import User
from app.utils.auth import admin_required, hash_password
from app.utils.response import success, error


VALID_ROLES = ('admin', 'user')


def _validate_payload(data, is_create=False):
    username = (data.get('username') or '').strip()
    role = data.get('role') or 'user'
    password = data.get('password') or ''

    if is_create:
        if not username:
            return '用户名不能为空'
        if not password or len(password) < 6:
            return '密码至少 6 位'
    if role not in VALID_ROLES:
        return f'role 必须是 {VALID_ROLES} 之一'
    return None


@api_bp.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    """分页列表，支持按用户名/昵称搜索"""
    keyword = (request.args.get('keyword') or '').strip()
    page = max(request.args.get('page', 1, type=int), 1)
    size = min(max(request.args.get('size', 10, type=int), 1), 100)

    query = User.query
    if keyword:
        like = f'%{keyword}%'
        query = query.filter(or_(User.username.like(like), User.nickname.like(like)))

    total = query.count()
    items = (
        query.order_by(User.id.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return success({
        'total': total,
        'page': page,
        'size': size,
        'items': [u.to_dict() for u in items],
    })


@api_bp.route('/admin/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json(silent=True) or {}
    err = _validate_payload(data, is_create=True)
    if err:
        return error(err)

    username = data['username'].strip()
    if User.query.filter_by(username=username).first():
        return error('用户名已存在', 409)

    user = User(
        username=username,
        password_hash=hash_password(data['password']),
        nickname=(data.get('nickname') or '').strip() or None,
        role=data.get('role') or 'user',
        phone=(data.get('phone') or '').strip() or None,
    )
    db.session.add(user)
    db.session.commit()
    return success(user.to_dict())


@api_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    data = request.get_json(silent=True) or {}
    err = _validate_payload(data, is_create=False)
    if err:
        return error(err)

    if 'nickname' in data:
        user.nickname = (data['nickname'] or '').strip() or None
    if 'phone' in data:
        user.phone = (data['phone'] or '').strip() or None
    if 'role' in data:
        # 禁止把自己降级
        if user.id == g.current_user['uid'] and data['role'] != 'admin':
            return error('不能降低自己的角色', 400)
        user.role = data['role']

    db.session.commit()
    return success(user.to_dict())


@api_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    if user_id == g.current_user['uid']:
        return error('不能删除当前登录的自己', 400)

    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    db.session.delete(user)
    db.session.commit()
    return success({'id': user_id})


@api_bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', 404)

    data = request.get_json(silent=True) or {}
    new_password = data.get('newPassword') or ''
    if len(new_password) < 6:
        return error('新密码至少 6 位')

    user.password_hash = hash_password(new_password)
    db.session.commit()
    return success({'id': user_id})
