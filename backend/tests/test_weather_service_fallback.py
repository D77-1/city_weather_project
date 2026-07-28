import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.weather_service import _build_history_from_forecast


forecast = [
    {
        'date': '2026-03-28',
        'tempMax': 18,
        'tempMin': 10,
        'precipitation': 2.5,
        'windSpeedMax': 12,
        'weatherCode': 3,
    },
    {
        'date': '2026-03-29',
        'tempMax': 20,
        'tempMin': 12,
        'precipitation': 0,
        'windSpeedMax': 10,
        'weatherCode': 1,
    },
]

history = _build_history_from_forecast(forecast)
assert len(history) == 2, '应从 forecast 构造两条历史记录'
assert history[0]['date'] == '2026-03-28'
assert history[0]['tempMean'] == 14.0, '应按最高/最低温构造均温'
assert history[0]['precipitation'] == 2.5
assert history[0]['weatherText'], '应补充天气描述'
assert history[0]['emoji'], '应补充天气图标'

print('weather fallback test passed')
