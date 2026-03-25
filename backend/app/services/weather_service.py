"""
天气数据服务 - 调用 Open-Meteo 免费 API 获取真实天气数据
无需 API Key，支持实时天气、7日预报、历史天气
文档: https://open-meteo.com/
"""
import requests
from datetime import datetime, timedelta
from functools import lru_cache

OPEN_METEO_BASE = 'https://api.open-meteo.com/v1/forecast'
OPEN_METEO_ARCHIVE = 'https://archive-api.open-meteo.com/v1/archive'

# WMO 天气代码 → 中文描述
WMO_CODE_MAP = {
    0: '晴', 1: '大部晴', 2: '多云', 3: '阴',
    45: '雾', 48: '霜雾',
    51: '小毛毛雨', 53: '毛毛雨', 55: '大毛毛雨',
    56: '冻毛毛雨', 57: '强冻毛毛雨',
    61: '小雨', 63: '中雨', 65: '大雨',
    66: '冻雨', 67: '强冻雨',
    71: '小雪', 73: '中雪', 75: '大雪', 77: '雪粒',
    80: '阵雨', 81: '中阵雨', 82: '强阵雨',
    85: '小阵雪', 86: '大阵雪',
    95: '雷暴', 96: '雷暴冰雹', 99: '强雷暴冰雹',
}


def _wmo_to_text(code):
    return WMO_CODE_MAP.get(code, '未知')


def _wmo_to_emoji(code):
    if code == 0:
        return '☀️'
    if code <= 2:
        return '⛅'
    if code == 3:
        return '☁️'
    if code in (45, 48):
        return '🌫️'
    if code in (51, 53, 55, 56, 57, 61, 63, 80, 81):
        return '🌦️'
    if code in (65, 66, 67, 82):
        return '🌧️'
    if code in (71, 73, 75, 77, 85, 86):
        return '🌨️'
    if code >= 95:
        return '⛈️'
    return '🌤️'


def get_realtime_weather(lat, lng):
    """
    获取实时天气
    返回: { temperature, humidity, windSpeed, windDirection, rainfall, pressure,
            weatherCode, weatherText, weatherEmoji, feelsLike, visibility, uvIndex }
    """
    try:
        resp = requests.get(OPEN_METEO_BASE, params={
            'latitude': lat, 'longitude': lng,
            'current': ','.join([
                'temperature_2m', 'relative_humidity_2m', 'apparent_temperature',
                'precipitation', 'weather_code', 'wind_speed_10m',
                'wind_direction_10m', 'surface_pressure',
            ]),
            'timezone': 'Asia/Shanghai',
        }, timeout=8)
        resp.raise_for_status()
        data = resp.json().get('current', {})
    except Exception as e:
        print(f'[Weather] 实时天气请求失败: {e}')
        return None

    code = data.get('weather_code', 0)
    wind_deg = data.get('wind_direction_10m', 0)
    dirs = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
    wind_dir = dirs[int((wind_deg + 22.5) / 45) % 8]

    return {
        'temperature': data.get('temperature_2m'),
        'feelsLike': data.get('apparent_temperature'),
        'humidity': data.get('relative_humidity_2m'),
        'windSpeed': data.get('wind_speed_10m'),
        'windDirection': wind_dir,
        'windDeg': wind_deg,
        'rainfall': data.get('precipitation', 0),
        'pressure': data.get('surface_pressure'),
        'weatherCode': code,
        'weatherText': _wmo_to_text(code),
        'weatherEmoji': _wmo_to_emoji(code),
        'updateTime': data.get('time', ''),
    }


def get_weather_forecast(lat, lng, days=7):
    """
    获取未来 N 天天气预报
    返回: [{ date, tempMax, tempMin, weatherText, emoji, precipitation,
             windSpeedMax, humidity, uvIndexMax, sunrise, sunset }]
    """
    try:
        resp = requests.get(OPEN_METEO_BASE, params={
            'latitude': lat, 'longitude': lng,
            'daily': ','.join([
                'temperature_2m_max', 'temperature_2m_min', 'weather_code',
                'precipitation_sum', 'wind_speed_10m_max',
                'relative_humidity_2m_mean', 'uv_index_max',
                'sunrise', 'sunset',
            ]),
            'timezone': 'Asia/Shanghai',
            'forecast_days': min(days, 16),
        }, timeout=8)
        resp.raise_for_status()
        daily = resp.json().get('daily', {})
    except Exception as e:
        print(f'[Weather] 天气预报请求失败: {e}')
        return []

    dates = daily.get('time', [])
    result = []
    for i, date in enumerate(dates):
        code = daily['weather_code'][i] if daily.get('weather_code') else 0
        result.append({
            'date': date,
            'dateShort': date[5:],  # MM-DD
            'weekday': _weekday_cn(date),
            'tempMax': daily.get('temperature_2m_max', [None])[i],
            'tempMin': daily.get('temperature_2m_min', [None])[i],
            'weatherCode': code,
            'weatherText': _wmo_to_text(code),
            'emoji': _wmo_to_emoji(code),
            'precipitation': daily.get('precipitation_sum', [0])[i] or 0,
            'windSpeedMax': daily.get('wind_speed_10m_max', [None])[i],
            'humidity': daily.get('relative_humidity_2m_mean', [None])[i],
            'uvIndexMax': daily.get('uv_index_max', [None])[i],
            'sunrise': (daily.get('sunrise', [''])[i] or '')[-5:],
            'sunset': (daily.get('sunset', [''])[i] or '')[-5:],
        })

    return result


def get_weather_history(lat, lng, days=30):
    """
    获取过去 N 天的历史天气
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    try:
        resp = requests.get(OPEN_METEO_ARCHIVE, params={
            'latitude': lat, 'longitude': lng,
            'start_date': start_date,
            'end_date': end_date,
            'daily': ','.join([
                'temperature_2m_max', 'temperature_2m_min', 'temperature_2m_mean',
                'precipitation_sum', 'wind_speed_10m_max',
                'relative_humidity_2m_mean', 'weather_code',
            ]),
            'timezone': 'Asia/Shanghai',
        }, timeout=10)
        resp.raise_for_status()
        daily = resp.json().get('daily', {})
    except Exception as e:
        print(f'[Weather] 历史天气请求失败: {e}')
        return []

    dates = daily.get('time', [])
    result = []
    for i, date in enumerate(dates):
        code = (daily.get('weather_code') or [0])[i] or 0
        result.append({
            'date': date,
            'tempMax': (daily.get('temperature_2m_max') or [None])[i],
            'tempMin': (daily.get('temperature_2m_min') or [None])[i],
            'tempMean': (daily.get('temperature_2m_mean') or [None])[i],
            'precipitation': (daily.get('precipitation_sum') or [0])[i] or 0,
            'windSpeedMax': (daily.get('wind_speed_10m_max') or [None])[i],
            'humidity': (daily.get('relative_humidity_2m_mean') or [None])[i],
            'weatherText': _wmo_to_text(code),
            'emoji': _wmo_to_emoji(code),
        })

    return result


def _weekday_cn(date_str):
    days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        return days[d.weekday()]
    except Exception:
        return ''
