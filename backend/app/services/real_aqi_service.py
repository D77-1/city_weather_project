"""
真实空气质量数据服务 - Open-Meteo Air Quality API
提供全球实时 PM2.5/PM10/NO2/SO2/O3/CO 浓度
按中国国标 HJ 633-2012 计算 AQI

API 文档: https://open-meteo.com/en/docs/air-quality-api
"""
import requests
import math
from datetime import datetime

AQ_API = 'https://air-quality-api.open-meteo.com/v1/air-quality'

# ===== 中国 AQI 国标分段表 (HJ 633-2012) =====
# 格式: (浓度下限, 浓度上限, AQI下限, AQI上限)
# PM2.5: 24小时平均 (μg/m³)
PM25_BREAKPOINTS = [
    (0, 35, 0, 50), (35, 75, 50, 100), (75, 115, 100, 150),
    (115, 150, 150, 200), (150, 250, 200, 300), (250, 350, 300, 400), (350, 500, 400, 500),
]
# PM10: 24小时平均 (μg/m³)
PM10_BREAKPOINTS = [
    (0, 50, 0, 50), (50, 150, 50, 100), (150, 250, 100, 150),
    (250, 350, 150, 200), (350, 420, 200, 300), (420, 500, 300, 400), (500, 600, 400, 500),
]
# SO2: 24小时平均 (μg/m³)
SO2_BREAKPOINTS = [
    (0, 50, 0, 50), (50, 150, 50, 100), (150, 475, 100, 150),
    (475, 800, 150, 200), (800, 1600, 200, 300), (1600, 2100, 300, 400), (2100, 2620, 400, 500),
]
# NO2: 24小时平均 (μg/m³)
NO2_BREAKPOINTS = [
    (0, 40, 0, 50), (40, 80, 50, 100), (80, 180, 100, 150),
    (180, 280, 150, 200), (280, 565, 200, 300), (565, 750, 300, 400), (750, 940, 400, 500),
]
# CO: 24小时平均 (mg/m³)
CO_BREAKPOINTS = [
    (0, 2, 0, 50), (2, 4, 50, 100), (4, 14, 100, 150),
    (14, 24, 150, 200), (24, 36, 200, 300), (36, 48, 300, 400), (48, 60, 400, 500),
]
# O3: 8小时滑动平均 (μg/m³)
O3_BREAKPOINTS = [
    (0, 100, 0, 50), (100, 160, 50, 100), (160, 215, 100, 150),
    (215, 265, 150, 200), (265, 800, 200, 300),
]


def _calc_iaqi(concentration, breakpoints):
    """根据浓度和分段表计算单项 IAQI"""
    if concentration is None or concentration < 0:
        return None
    for c_lo, c_hi, i_lo, i_hi in breakpoints:
        if c_lo <= concentration <= c_hi:
            return round(((i_hi - i_lo) / (c_hi - c_lo)) * (concentration - c_lo) + i_lo)
    # 超出最高段
    return 500


def calc_china_aqi(pm25=None, pm10=None, so2=None, no2=None, co=None, o3=None):
    """
    按国标 HJ 633-2012 计算综合 AQI
    返回: { aqi, primaryPollutant, qualityLevel, iaqis: { pm25, pm10, so2, no2, co, o3 } }
    """
    pollutant_map = {
        'PM2.5': (pm25, PM25_BREAKPOINTS),
        'PM10': (pm10, PM10_BREAKPOINTS),
        'SO2': (so2, SO2_BREAKPOINTS),
        'NO2': (no2, NO2_BREAKPOINTS),
        'CO': (co, CO_BREAKPOINTS),
        'O3': (o3, O3_BREAKPOINTS),
    }

    iaqis = {}
    for name, (val, bp) in pollutant_map.items():
        iaqi = _calc_iaqi(val, bp)
        if iaqi is not None:
            iaqis[name] = iaqi

    if not iaqis:
        return None

    aqi = max(iaqis.values())
    primary = max(iaqis, key=iaqis.get) if aqi > 50 else None

    if aqi <= 50:
        level = '优'
    elif aqi <= 100:
        level = '良'
    elif aqi <= 150:
        level = '轻度污染'
    elif aqi <= 200:
        level = '中度污染'
    elif aqi <= 300:
        level = '重度污染'
    else:
        level = '严重污染'

    return {
        'aqi': aqi,
        'primaryPollutant': primary,
        'qualityLevel': level,
        'iaqis': iaqis,
    }


def get_realtime_aqi(lat, lng):
    """
    获取某坐标的实时空气质量（真实数据）
    返回: { pm25, pm10, so2, no2, co, o3, aqi, qualityLevel, primaryPollutant, updateTime, source }
    """
    try:
        resp = requests.get(AQ_API, params={
            'latitude': lat,
            'longitude': lng,
            'current': ','.join([
                'pm2_5', 'pm10', 'nitrogen_dioxide', 'sulphur_dioxide',
                'ozone', 'carbon_monoxide',
            ]),
            'timezone': 'Asia/Shanghai',
        }, timeout=8)
        resp.raise_for_status()
        current = resp.json().get('current', {})
    except Exception as e:
        print(f'[RealAQI] 请求失败: {e}')
        return None

    pm25 = current.get('pm2_5')
    pm10 = current.get('pm10')
    so2 = current.get('sulphur_dioxide')
    no2 = current.get('nitrogen_dioxide')
    # Open-Meteo 返回 μg/m³，CO 国标用 mg/m³，需除以 1000
    co_ugm3 = current.get('carbon_monoxide')
    co = round(co_ugm3 / 1000, 1) if co_ugm3 is not None else None
    o3 = current.get('ozone')

    aqi_result = calc_china_aqi(pm25, pm10, so2, no2, co, o3)

    return {
        'pm25': round(pm25, 1) if pm25 is not None else None,
        'pm10': round(pm10, 1) if pm10 is not None else None,
        'so2': round(so2, 1) if so2 is not None else None,
        'no2': round(no2, 1) if no2 is not None else None,
        'co': co,
        'o3': round(o3, 1) if o3 is not None else None,
        'aqi': aqi_result['aqi'] if aqi_result else None,
        'qualityLevel': aqi_result['qualityLevel'] if aqi_result else None,
        'primaryPollutant': aqi_result['primaryPollutant'] if aqi_result else None,
        'iaqis': aqi_result['iaqis'] if aqi_result else {},
        'updateTime': current.get('time', ''),
        'source': 'Open-Meteo (CAMS)',
    }


def get_aqi_forecast(lat, lng, days=5):
    """
    获取未来 N 天逐小时空气质量预报，聚合为日均值
    返回: [{ date, pm25, pm10, so2, no2, co, o3, aqi, qualityLevel }]
    """
    try:
        resp = requests.get(AQ_API, params={
            'latitude': lat,
            'longitude': lng,
            'hourly': 'pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,ozone,carbon_monoxide',
            'timezone': 'Asia/Shanghai',
            'forecast_days': min(days, 5),
        }, timeout=10)
        resp.raise_for_status()
        hourly = resp.json().get('hourly', {})
    except Exception as e:
        print(f'[RealAQI] 预报请求失败: {e}')
        return []

    times = hourly.get('time', [])
    if not times:
        return []

    # 按日期聚合
    daily = {}
    for i, t in enumerate(times):
        date = t[:10]
        if date not in daily:
            daily[date] = {'pm25': [], 'pm10': [], 'so2': [], 'no2': [], 'co': [], 'o3': []}
        d = daily[date]
        if hourly.get('pm2_5') and hourly['pm2_5'][i] is not None:
            d['pm25'].append(hourly['pm2_5'][i])
        if hourly.get('pm10') and hourly['pm10'][i] is not None:
            d['pm10'].append(hourly['pm10'][i])
        if hourly.get('sulphur_dioxide') and hourly['sulphur_dioxide'][i] is not None:
            d['so2'].append(hourly['sulphur_dioxide'][i])
        if hourly.get('nitrogen_dioxide') and hourly['nitrogen_dioxide'][i] is not None:
            d['no2'].append(hourly['nitrogen_dioxide'][i])
        if hourly.get('carbon_monoxide') and hourly['carbon_monoxide'][i] is not None:
            d['co'].append(hourly['carbon_monoxide'][i] / 1000)  # μg → mg
        if hourly.get('ozone') and hourly['ozone'][i] is not None:
            d['o3'].append(hourly['ozone'][i])

    result = []
    for date in sorted(daily.keys()):
        d = daily[date]
        avg = lambda arr: round(sum(arr) / len(arr), 1) if arr else None
        pm25 = avg(d['pm25'])
        pm10 = avg(d['pm10'])
        so2 = avg(d['so2'])
        no2 = avg(d['no2'])
        co = avg(d['co'])
        o3 = avg(d['o3'])

        aqi_r = calc_china_aqi(pm25, pm10, so2, no2, co, o3)
        result.append({
            'date': date,
            'dateShort': date[5:],
            'pm25': pm25, 'pm10': pm10, 'so2': so2, 'no2': no2, 'co': co, 'o3': o3,
            'aqi': aqi_r['aqi'] if aqi_r else None,
            'qualityLevel': aqi_r['qualityLevel'] if aqi_r else None,
            'primaryPollutant': aqi_r['primaryPollutant'] if aqi_r else None,
            'source': 'Open-Meteo (CAMS)',
        })

    return result


def get_aqi_history(lat, lng, days=30):
    """
    获取过去 N 天逐小时历史空气质量，聚合为日均值
    使用 Open-Meteo 历史空气质量 API
    """
    from datetime import timedelta
    end = datetime.now().strftime('%Y-%m-%d')
    start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    ARCHIVE_AQ = 'https://air-quality-api.open-meteo.com/v1/air-quality'

    try:
        resp = requests.get(ARCHIVE_AQ, params={
            'latitude': lat,
            'longitude': lng,
            'hourly': 'pm2_5,pm10,nitrogen_dioxide,sulphur_dioxide,ozone,carbon_monoxide',
            'timezone': 'Asia/Shanghai',
            'start_date': start,
            'end_date': end,
            'past_days': days,
        }, timeout=15)
        resp.raise_for_status()
        hourly = resp.json().get('hourly', {})
    except Exception as e:
        print(f'[RealAQI] 历史请求失败: {e}')
        return []

    times = hourly.get('time', [])
    if not times:
        return []

    # 同样按日聚合
    daily = {}
    for i, t in enumerate(times):
        date = t[:10]
        if date not in daily:
            daily[date] = {'pm25': [], 'pm10': [], 'so2': [], 'no2': [], 'co': [], 'o3': []}
        d = daily[date]
        if hourly.get('pm2_5') and i < len(hourly['pm2_5']) and hourly['pm2_5'][i] is not None:
            d['pm25'].append(hourly['pm2_5'][i])
        if hourly.get('pm10') and i < len(hourly['pm10']) and hourly['pm10'][i] is not None:
            d['pm10'].append(hourly['pm10'][i])
        if hourly.get('sulphur_dioxide') and i < len(hourly['sulphur_dioxide']) and hourly['sulphur_dioxide'][i] is not None:
            d['so2'].append(hourly['sulphur_dioxide'][i])
        if hourly.get('nitrogen_dioxide') and i < len(hourly['nitrogen_dioxide']) and hourly['nitrogen_dioxide'][i] is not None:
            d['no2'].append(hourly['nitrogen_dioxide'][i])
        if hourly.get('carbon_monoxide') and i < len(hourly['carbon_monoxide']) and hourly['carbon_monoxide'][i] is not None:
            d['co'].append(hourly['carbon_monoxide'][i] / 1000)
        if hourly.get('ozone') and i < len(hourly['ozone']) and hourly['ozone'][i] is not None:
            d['o3'].append(hourly['ozone'][i])

    result = []
    for date in sorted(daily.keys()):
        d = daily[date]
        avg = lambda arr: round(sum(arr) / len(arr), 1) if arr else None
        pm25 = avg(d['pm25'])
        pm10 = avg(d['pm10'])
        so2 = avg(d['so2'])
        no2 = avg(d['no2'])
        co = avg(d['co'])
        o3 = avg(d['o3'])
        aqi_r = calc_china_aqi(pm25, pm10, so2, no2, co, o3)
        result.append({
            'date': date,
            'pm25': pm25, 'pm10': pm10, 'so2': so2, 'no2': no2, 'co': co, 'o3': o3,
            'aqi': aqi_r['aqi'] if aqi_r else None,
            'qualityLevel': aqi_r['qualityLevel'] if aqi_r else None,
        })

    return result
