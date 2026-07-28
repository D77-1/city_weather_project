"""
鉴权与权限装饰器测试
运行: D:/conda_envs/python3.12/python.exe backend/tests/test_auth.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app

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


def login(username='admin', password='admin123'):
    resp = client.post('/api/auth/login', json={
        'username': username, 'password': password,
    })
    data = resp.get_json() or {}
    if resp.status_code == 200 and data.get('code') == 200:
        return data['data']['token']
    return None


print('=' * 50)
print('鉴权与装饰器测试')
print('=' * 50)

# 1. 登录
print('\n[1] 登录接口')
token = login()
check('正确账密能登录拿到 token', bool(token))

resp = client.post('/api/auth/login', json={'username': 'admin', 'password': 'wrong'})
check('错误密码返回 401', resp.status_code == 401, f'实际 status={resp.status_code}')

resp = client.post('/api/auth/login', json={'username': 'notexist', 'password': 'x'})
check('不存在的用户返回 401', resp.status_code == 401)

resp = client.post('/api/auth/login', json={})
check('空参数返回 400', resp.status_code == 400)

# 2. /auth/me
print('\n[2] /auth/me')
resp = client.get('/api/auth/me')
check('无 token 调 /auth/me 返 401', resp.status_code == 401)

resp = client.get('/api/auth/me', headers={'Authorization': f'Bearer {token}'})
data = resp.get_json() or {}
check('带 token 调 /auth/me 返当前用户', resp.status_code == 200 and data.get('data', {}).get('username') == 'admin')

resp = client.get('/api/auth/me', headers={'Authorization': 'Bearer invalid.token.here'})
check('无效 token 返 401', resp.status_code == 401)

# 3. admin_required
print('\n[3] admin_required 装饰器')
resp = client.get('/api/admin/users')
check('无 token 调 /admin/users 返 401', resp.status_code == 401)

resp = client.get('/api/admin/users', headers={'Authorization': f'Bearer {token}'})
check('admin token 可访问 /admin/users', resp.status_code == 200)

resp = client.get('/api/admin/stats', headers={'Authorization': f'Bearer {token}'})
check('admin token 可访问 /admin/stats', resp.status_code == 200)

# 4. 游客读接口继续开放
print('\n[4] 游客读接口保持开放')
resp = client.get('/api/cities')
check('GET /cities 无需登录', resp.status_code == 200)

resp = client.get('/api/anomaly/list')
check('GET /anomaly/list 无需登录', resp.status_code == 200)

# 5. 受保护写接口
print('\n[5] 写接口鉴权')
resp = client.post('/api/anomaly/detect', json={'cityId': 1})
check('POST /anomaly/detect 无 token 返 401', resp.status_code == 401)

resp = client.put('/api/anomaly/999999/status', json={'status': 'dismissed'})
check('PUT /anomaly/<id>/status 无 token 返 401', resp.status_code == 401)

# 6. 游客仍可用的计算接口
print('\n[6] 游客可用的计算接口')
resp = client.post('/api/risk/assess', json={'cityId': 1})
check('POST /risk/assess 游客可用', resp.status_code == 200)

print('\n' + '=' * 50)
print(f'总计: {PASS + FAIL}  通过: {PASS}  失败: {FAIL}')
print('=' * 50)

sys.exit(0 if FAIL == 0 else 1)
