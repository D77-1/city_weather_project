"""
后端 API 自动化测试脚本
运行: D:/conda_envs/python3.12/python.exe backend/tests/test_api.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db

app = create_app()
client = app.test_client()

PASS = 0
FAIL = 0


def assert_true(condition, msg=""):
    if not condition:
        raise AssertionError(msg)


def test(name, response, checks=None):
    global PASS, FAIL
    ok = response.status_code == 200
    data = response.get_json()
    if ok and data:
        ok = data.get('code') == 200
    if ok and checks:
        try:
            checks(data.get('data'))
        except Exception as e:
            ok = False
            print(f"  [FAIL] {name}: 断言失败 - {e}")
    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} (status={response.status_code})")


print("=" * 50)
print("后端 API 测试")
print("=" * 50)

# --- 城市相关 ---
print("\n[城市 API]")
test("GET /api/cities", client.get('/api/cities'),
     lambda d: assert_true(len(d) >= 20, f"城市数={len(d)}"))

test("GET /api/cities/1", client.get('/api/cities/1'),
     lambda d: assert_true(d['name'], "有城市名"))

test("GET /api/cities/1/stations", client.get('/api/cities/1/stations'),
     lambda d: assert_true(len(d) >= 1, f"站点数={len(d)}"))

test("GET /api/provinces", client.get('/api/provinces'),
     lambda d: assert_true(len(d) >= 5, f"省份数={len(d)}"))

# --- 空气质量 ---
print("\n[空气质量 API]")
test("GET /api/air-quality/latest", client.get('/api/air-quality/latest'),
     lambda d: assert_true(len(d) >= 20 and 'temperature' in d[0] and 'recordDate' in d[0], "有时间与天气字段"))

test("GET /api/realtime-all", client.get('/api/realtime-all?city_id=1'),
     lambda d: assert_true('source' in d and 'airQuality' in d and 'weather' in d, "有实时组合数据"))

test("GET /api/weather/history", client.get('/api/weather/history?city_id=1&days=7'),
     lambda d: assert_true('history' in d and isinstance(d['history'], list), "有天气历史数据"))

test("GET /api/aqi-history-real", client.get('/api/aqi-history-real?city_id=1&days=7'),
     lambda d: assert_true('history' in d and isinstance(d['history'], list), "有真实AQI历史数据"))


test("GET /api/air-quality/history (30天)", client.get('/api/air-quality/history?city_id=1&days=30'),
     lambda d: assert_true(len(d) >= 25, f"记录数={len(d)}"))

test("GET /api/air-quality/ranking", client.get('/api/air-quality/ranking?order=desc&limit=10'),
     lambda d: assert_true(len(d) == 10 and d[0]['aqi'] >= d[-1]['aqi'], "排序正确"))

test("GET /api/air-quality/map-data", client.get('/api/air-quality/map-data'),
     lambda d: assert_true(len(d) >= 20 and len(d[0]['value']) == 3, "有坐标+AQI"))

# --- 预测 ---
print("\n[预测 API]")
test("POST /api/prediction/run",
     client.post('/api/prediction/run', json={'cityId': 1, 'metric': 'aqi', 'window': 7, 'forecastDays': 7}),
     lambda d: assert_true('predictions' in d and len(d['predictions']) == 7, "7天预测"))

# --- 异常检测 ---
print("\n[异常检测 API]")
test("POST /api/anomaly/detect",
     client.post('/api/anomaly/detect', json={'cityId': 1, 'metric': 'aqi', 'days': 90}),
     lambda d: assert_true('q1' in d and 'anomaly_count' in d, "有IQR结果"))

# --- AI ---
print("\n[AI API]")
test("POST /api/ai/advice",
     client.post('/api/ai/advice', json={
         'message': '测试', 'sessionId': 'test-001', 'cityId': 1, 'context': {}
     }),
     lambda d: assert_true('content' in d, "有AI回复"))

# --- 汇总 ---
print("\n" + "=" * 50)
print(f"结果: {PASS} 通过, {FAIL} 失败, 共 {PASS + FAIL} 项")
print("=" * 50)
