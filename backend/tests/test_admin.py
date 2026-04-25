"""
管理员模块 CRUD / 批量审核 / 统计测试
运行: D:/conda_envs/python3.12/python.exe backend/tests/test_admin.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import AnomalyEvent

app = create_app()
client = app.test_client()

PASS = 0
FAIL = 0


def check(name, cond, info=''):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} {info}')


def bearer():
    resp = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
    return {'Authorization': f'Bearer {resp.get_json()["data"]["token"]}'}


print('=' * 50)
print('管理员模块测试')
print('=' * 50)

headers = bearer()

# 1. 用户 CRUD
print('\n[1] 用户管理')
new_user_name = 'test_auto_user_42'

# 清理可能遗留的测试用户
with app.app_context():
    from app.models import User
    stale = User.query.filter_by(username=new_user_name).first()
    if stale:
        db.session.delete(stale)
        db.session.commit()

resp = client.post('/api/admin/users', headers=headers, json={
    'username': new_user_name, 'password': 'test1234', 'nickname': '自动化测试', 'role': 'user',
})
data = resp.get_json() or {}
new_id = data.get('data', {}).get('id')
check('创建新用户', resp.status_code == 200 and new_id)

resp = client.get('/api/admin/users', headers=headers, query_string={'keyword': 'test_auto'})
data = resp.get_json() or {}
check('搜索列表能命中新用户', data.get('data', {}).get('total', 0) >= 1)

resp = client.put(f'/api/admin/users/{new_id}', headers=headers, json={
    'nickname': '已改昵称', 'role': 'user',
})
check('更新用户', resp.status_code == 200)

resp = client.post(
    f'/api/admin/users/{new_id}/reset-password', headers=headers, json={'newPassword': 'newPass99'}
)
check('重置密码', resp.status_code == 200)

# 验证新密码能登录
resp = client.post('/api/auth/login', json={'username': new_user_name, 'password': 'newPass99'})
# 因为 role=user，登录会被 403 拒绝（当前仅 admin 允许登录后台），但能验证密码对
check(
    '新密码验证（user 角色被 403）',
    resp.status_code in (200, 403),
    f'实际 status={resp.status_code}',
)

resp = client.delete(f'/api/admin/users/{new_id}', headers=headers)
check('删除用户', resp.status_code == 200)

# 2. 不能删除自己
print('\n[2] 安全约束')
with app.app_context():
    from app.models import User
    admin_id = User.query.filter_by(username='admin').first().id
resp = client.delete(f'/api/admin/users/{admin_id}', headers=headers)
check('禁止删除当前登录用户', resp.status_code == 400)

# 3. 批量审核
print('\n[3] 批量审核')
with app.app_context():
    sample = AnomalyEvent.query.limit(2).all()
    sample_ids = [e.id for e in sample]

if sample_ids:
    resp = client.post('/api/admin/anomalies/batch-review', headers=headers, json={
        'ids': sample_ids, 'action': 'confirmed',
    })
    check('批量确认异常', resp.status_code == 200)

    with app.app_context():
        for e in AnomalyEvent.query.filter(AnomalyEvent.id.in_(sample_ids)).all():
            check(
                f'事件 {e.id} 状态已更新并留痕',
                e.status == 'confirmed' and e.reviewed_by == admin_id and e.reviewed_at is not None,
            )
else:
    print('  [SKIP] 数据库内无异常事件，跳过批量审核测试')

# 4. 仪表盘指标
print('\n[4] 仪表盘指标')
resp = client.get('/api/admin/stats', headers=headers)
data = resp.get_json() or {}
payload = data.get('data') or {}
required_keys = [
    'totalRecords', 'activeCities', 'activeStations',
    'anomalies', 'aiCalls', 'users', 'anomalyTrend7d',
]
missing = [k for k in required_keys if k not in payload]
check('仪表盘返回所有必需字段', not missing, f'缺失: {missing}')
check('anomalies 子结构', isinstance(payload.get('anomalies'), dict))

# 5. AI 日志
print('\n[5] AI 日志审计')
resp = client.get('/api/admin/ai-logs', headers=headers)
check('列表接口 200', resp.status_code == 200)

print('\n' + '=' * 50)
print(f'总计: {PASS + FAIL}  通过: {PASS}  失败: {FAIL}')
print('=' * 50)

sys.exit(0 if FAIL == 0 else 1)
