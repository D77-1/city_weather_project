"""
空气质量数据服务 - 调用 Open-Meteo Air Quality API 获取真实历史数据
无需 API Key，数据源: CAMS 全球大气成分预报
文档: https://open-meteo.com/en/docs/air-quality-api
"""
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app import db
from app.models import City, MonitoringStation, AirQualityRecord

AQ_API_BASE = 'https://air-quality-api.open-meteo.com/v1/air-quality'
REQUEST_TIMEOUT = 30

# Open-Meteo 请求的小时级变量
HOURLY_VARS = ','.join([
    'pm2_5', 'pm10',
    'nitrogen_dioxide', 'sulphur_dioxide', 'ozone', 'carbon_monoxide',
    'us_aqi', 'us_aqi_pm2_5', 'us_aqi_pm10',
    'us_aqi_nitrogen_dioxide', 'us_aqi_ozone',
    'us_aqi_sulphur_dioxide', 'us_aqi_carbon_monoxide',
])

QUALITY_LEVELS = [
    (0, 50, '优'), (51, 100, '良'), (101, 150, '轻度污染'),
    (151, 200, '中度污染'), (201, 300, '重度污染'), (301, 500, '严重污染'),
]

# 中国 AQI 标准 HJ 633-2012 分段表
# (浓度下限, 浓度上限, AQI下限, AQI上限)
# PM2.5 24h均值 (μg/m³), PM10 24h均值 (μg/m³), SO2 24h均值 (μg/m³),
# NO2 24h均值 (μg/m³), CO 24h均值 (mg/m³), O3 8h滑动均值 (μg/m³)
CN_AQI_BREAKPOINTS = {
    'pm25': [(0, 35, 0, 50), (35, 75, 50, 100), (75, 115, 100, 150),
             (115, 150, 150, 200), (150, 250, 200, 300), (250, 350, 300, 400), (350, 500, 400, 500)],
    'pm10': [(0, 50, 0, 50), (50, 150, 50, 100), (150, 250, 100, 150),
             (250, 350, 150, 200), (350, 420, 200, 300), (420, 500, 300, 400), (500, 600, 400, 500)],
    'so2':  [(0, 50, 0, 50), (50, 150, 50, 100), (150, 475, 100, 150),
             (475, 800, 150, 200), (800, 1600, 200, 300), (1600, 2100, 300, 400), (2100, 2620, 400, 500)],
    'no2':  [(0, 40, 0, 50), (40, 80, 50, 100), (80, 180, 100, 150),
             (180, 280, 150, 200), (280, 565, 200, 300), (565, 750, 300, 400), (750, 940, 400, 500)],
    'co':   [(0, 2, 0, 50), (2, 4, 50, 100), (4, 14, 100, 150),
             (14, 24, 150, 200), (24, 36, 200, 300), (36, 48, 300, 400), (48, 60, 400, 500)],
    'o3':   [(0, 100, 0, 50), (100, 160, 50, 100), (160, 215, 100, 150),
             (215, 265, 150, 200), (265, 800, 200, 300), (800, 1000, 300, 400), (1000, 1200, 400, 500)],
}


def _calc_iaqi(concentration, breakpoints):
    """根据中国标准计算单项 IAQI"""
    if concentration is None or concentration < 0:
        return None
    for c_low, c_high, i_low, i_high in breakpoints:
        if c_low <= concentration <= c_high:
            return round(i_low + (concentration - c_low) / (c_high - c_low) * (i_high - i_low))
    # 超出最高范围
    if concentration > breakpoints[-1][1]:
        return 500
    return None


def _calc_cn_aqi(pm25=None, pm10=None, so2=None, no2=None, co=None, o3=None):
    """
    根据中国 HJ 633-2012 标准计算综合 AQI
    AQI = max(各项 IAQI)
    """
    iaqis = {}
    if pm25 is not None:
        iaqis['PM2.5'] = _calc_iaqi(pm25, CN_AQI_BREAKPOINTS['pm25'])
    if pm10 is not None:
        iaqis['PM10'] = _calc_iaqi(pm10, CN_AQI_BREAKPOINTS['pm10'])
    if so2 is not None:
        iaqis['SO2'] = _calc_iaqi(so2, CN_AQI_BREAKPOINTS['so2'])
    if no2 is not None:
        iaqis['NO2'] = _calc_iaqi(no2, CN_AQI_BREAKPOINTS['no2'])
    if co is not None:
        iaqis['CO'] = _calc_iaqi(co, CN_AQI_BREAKPOINTS['co'])
    if o3 is not None:
        iaqis['O3'] = _calc_iaqi(o3, CN_AQI_BREAKPOINTS['o3'])

    valid = {k: v for k, v in iaqis.items() if v is not None}
    if not valid:
        return None, 'PM2.5'
    aqi = max(valid.values())
    primary = max(valid, key=valid.get)
    return aqi, primary


def _aqi_to_level(aqi):
    if aqi is None:
        return '良'
    for low, high, level in QUALITY_LEVELS:
        if low <= aqi <= high:
            return level
    return '严重污染' if aqi > 500 else '良'


def _determine_primary_pollutant(pm25, pm10, so2, no2, co, o3):
    pollutants = {
        'PM2.5': pm25 or 0, 'PM10': pm10 or 0, 'SO2': so2 or 0,
        'NO2': no2 or 0, 'CO': (co or 0) * 1000, 'O3': o3 or 0,
    }
    return max(pollutants, key=pollutants.get)


def fetch_city_aqi_history(lat, lng, start_date, end_date):
    """
    拉取指定城市、指定时间段的逐小时空气质量数据
    返回 pandas DataFrame，index 为时间，columns 为各污染物
    """
    params = {
        'latitude': lat,
        'longitude': lng,
        'hourly': HOURLY_VARS,
        'start_date': start_date,
        'end_date': end_date,
        'timezone': 'Asia/Shanghai',
    }

    resp = requests.get(AQ_API_BASE, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    hourly = data.get('hourly', {})
    if not hourly or not hourly.get('time'):
        return pd.DataFrame()

    df = pd.DataFrame({
        'time': pd.to_datetime(hourly['time']),
        'pm25': hourly.get('pm2_5'),
        'pm10': hourly.get('pm10'),
        'no2': hourly.get('nitrogen_dioxide'),
        'so2': hourly.get('sulphur_dioxide'),
        'o3': hourly.get('ozone'),
        'co_ug': hourly.get('carbon_monoxide'),  # μg/m³
        'us_aqi': hourly.get('us_aqi'),
    })

    return df


def _hourly_to_daily(df):
    """
    逐小时数据 → 日均值
    返回 list of dict，每条代表一天
    """
    if df.empty:
        return []

    df = df.set_index('time')
    daily = df.resample('D').mean(numeric_only=True)
    daily = daily.dropna(how='all')

    records = []
    for date, row in daily.iterrows():
        pm25 = round(row['pm25'], 1) if pd.notna(row['pm25']) else None
        pm10 = round(row['pm10'], 1) if pd.notna(row['pm10']) else None
        so2 = round(row['so2'], 1) if pd.notna(row['so2']) else None
        no2 = round(row['no2'], 1) if pd.notna(row['no2']) else None
        co_ug = row['co_ug']
        co = round(co_ug / 1000, 2) if pd.notna(co_ug) else None  # μg→mg
        o3 = round(row['o3'], 1) if pd.notna(row['o3']) else None

        # 用中国标准 HJ 633-2012 计算 AQI（不再用 US AQI）
        aqi, primary = _calc_cn_aqi(pm25, pm10, so2, no2, co, o3)

        records.append({
            'date': date.date(),
            'aqi': aqi,
            'pm25': pm25,
            'pm10': pm10,
            'so2': so2,
            'no2': no2,
            'co': co,
            'o3': o3,
            'primary_pollutant': primary,
            'quality_level': _aqi_to_level(aqi),
        })

    return records


def _date_chunks(start_date, end_date, chunk_days=90):
    """将日期范围切成多个 chunk，每个不超过 chunk_days 天"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    chunks = []
    while start < end:
        chunk_end = min(start + timedelta(days=chunk_days - 1), end)
        chunks.append((start.strftime('%Y-%m-%d'), chunk_end.strftime('%Y-%m-%d')))
        start = chunk_end + timedelta(days=1)
    return chunks


def import_city_data(city, stations, start_date, end_date):
    """
    导入单个城市的空气质量数据
    对该城市的每个站点，使用城市经纬度+小偏移获取数据
    返回导入的记录数
    """
    lat, lng = float(city.latitude), float(city.longitude)
    chunks = _date_chunks(start_date, end_date)
    total = 0

    for station in stations:
        # 每个站点用略微不同的经纬度，模拟不同位置的差异
        s_lat = float(station.latitude)
        s_lng = float(station.longitude)

        station_records = []
        for chunk_start, chunk_end in chunks:
            try:
                df = fetch_city_aqi_history(s_lat, s_lng, chunk_start, chunk_end)
                daily_records = _hourly_to_daily(df)
                station_records.extend(daily_records)
                time.sleep(0.3)  # 限速，避免被封
            except Exception as e:
                print(f'  [Warning] {city.name}/{station.station_name} {chunk_start}~{chunk_end}: {e}')
                time.sleep(1)
                continue

        # 批量写入数据库
        db_records = []
        for rec in station_records:
            db_records.append(AirQualityRecord(
                station_id=station.id,
                city_id=city.id,
                record_time=datetime.combine(rec['date'], datetime.min.time()),
                record_type='daily',
                aqi=rec['aqi'],
                pm25=rec['pm25'],
                pm10=rec['pm10'],
                so2=rec['so2'],
                no2=rec['no2'],
                co=rec['co'],
                o3=rec['o3'],
                primary_pollutant=rec['primary_pollutant'],
                quality_level=rec['quality_level'],
            ))

        if db_records:
            db.session.bulk_save_objects(db_records)
            db.session.commit()
            total += len(db_records)
            print(f'  {station.station_name}: {len(db_records)} 条')

    return total


def import_all_cities(start_date='2022-09-01', end_date=None):
    """
    遍历所有城市，批量导入真实空气质量数据
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    cities = City.query.all()
    if not cities:
        print('[AQI Import] 数据库中没有城市数据，请先执行 flask seed')
        return 0

    grand_total = 0
    for i, city in enumerate(cities, 1):
        print(f'[{i}/{len(cities)}] {city.name} ({city.province})')
        stations = MonitoringStation.query.filter_by(city_id=city.id).all()
        if not stations:
            print(f'  跳过: 没有监测站点')
            continue

        count = import_city_data(city, stations, start_date, end_date)
        grand_total += count
        print(f'  小计: {count} 条')

    print(f'\n[AQI Import] 导入完成! 共 {grand_total} 条真实空气质量记录')
    print(f'  数据范围: {start_date} ~ {end_date}')
    print(f'  数据来源: Open-Meteo CAMS 全球大气模型')
    return grand_total


def fill_gaps(start_date='2022-09-01', end_date=None, max_retries=3):
    """
    检测并补充每个站点缺失的日期数据
    只请求缺口部分，不重复导入已有数据
    """
    from sqlalchemy import func
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    cities = City.query.all()
    grand_total = 0

    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    all_dates = set()
    d = start_dt
    while d <= end_dt:
        all_dates.add(d)
        d += timedelta(days=1)

    for i, city in enumerate(cities, 1):
        stations = MonitoringStation.query.filter_by(city_id=city.id).all()
        if not stations:
            continue

        city_total = 0
        for station in stations:
            # 查询该站点已有的日期
            existing = db.session.query(
                func.date(AirQualityRecord.record_time)
            ).filter(
                AirQualityRecord.station_id == station.id,
                AirQualityRecord.record_time >= start_date,
            ).all()
            existing_dates = {row[0] for row in existing}

            missing_dates = sorted(all_dates - existing_dates)
            if not missing_dates:
                continue

            # 将缺失日期合并成连续区间
            ranges = []
            range_start = missing_dates[0]
            prev = missing_dates[0]
            for md in missing_dates[1:]:
                if (md - prev).days > 1:
                    ranges.append((range_start, prev))
                    range_start = md
                prev = md
            ranges.append((range_start, prev))

            station_count = 0
            s_lat, s_lng = float(station.latitude), float(station.longitude)

            for r_start, r_end in ranges:
                chunks = _date_chunks(r_start.strftime('%Y-%m-%d'), r_end.strftime('%Y-%m-%d'))
                for chunk_start, chunk_end in chunks:
                    for attempt in range(max_retries):
                        try:
                            df = fetch_city_aqi_history(s_lat, s_lng, chunk_start, chunk_end)
                            daily_records = _hourly_to_daily(df)
                            db_records = []
                            for rec in daily_records:
                                if rec['date'] not in existing_dates:
                                    db_records.append(AirQualityRecord(
                                        station_id=station.id,
                                        city_id=city.id,
                                        record_time=datetime.combine(rec['date'], datetime.min.time()),
                                        record_type='daily',
                                        aqi=rec['aqi'], pm25=rec['pm25'], pm10=rec['pm10'],
                                        so2=rec['so2'], no2=rec['no2'], co=rec['co'], o3=rec['o3'],
                                        primary_pollutant=rec['primary_pollutant'],
                                        quality_level=rec['quality_level'],
                                    ))
                                    existing_dates.add(rec['date'])
                            if db_records:
                                db.session.bulk_save_objects(db_records)
                                db.session.commit()
                                station_count += len(db_records)
                            time.sleep(0.5)
                            break  # 成功，跳出重试
                        except Exception as e:
                            if attempt < max_retries - 1:
                                time.sleep(2 * (attempt + 1))
                            else:
                                print(f'  [Failed] {city.name}/{station.station_name} {chunk_start}~{chunk_end}: {e}')

            if station_count > 0:
                print(f'  {station.station_name}: +{station_count} 条')
                city_total += station_count

        if city_total > 0:
            print(f'[{i}/{len(cities)}] {city.name}: 补充 {city_total} 条')
            grand_total += city_total

    print(f'\n[AQI Fill] 缺口补充完成! 共补充 {grand_total} 条')
    return grand_total


def refresh_realtime():
    """
    启动时自动补充最新空气质量数据到今天
    轻量级：只补缺口天数，每个城市只请求一次，快速完成
    """
    from sqlalchemy import func
    latest = db.session.query(func.max(AirQualityRecord.record_time)).scalar()
    if not latest:
        print('[AQI] 数据库为空，请先执行 flask import-aqi')
        return 0

    today = datetime.now().strftime('%Y-%m-%d')
    last_date = (latest + timedelta(days=1)).strftime('%Y-%m-%d')

    if last_date > today:
        print('[AQI] 数据已是最新')
        return 0

    gap_days = (datetime.now() - latest).days
    print(f'[AQI] 自动补充 {gap_days} 天数据: {last_date} → {today}')

    cities = City.query.all()
    total = 0
    for city in cities:
        stations = MonitoringStation.query.filter_by(city_id=city.id).all()
        if not stations:
            continue
        try:
            # 每个城市只用第一个站点的经纬度请求一次
            lat, lng = float(stations[0].latitude), float(stations[0].longitude)
            df = fetch_city_aqi_history(lat, lng, last_date, today)
            daily_records = _hourly_to_daily(df)

            # 分配给所有站点
            db_records = []
            for station in stations:
                for rec in daily_records:
                    db_records.append(AirQualityRecord(
                        station_id=station.id,
                        city_id=city.id,
                        record_time=datetime.combine(rec['date'], datetime.min.time()),
                        record_type='daily',
                        aqi=rec['aqi'], pm25=rec['pm25'], pm10=rec['pm10'],
                        so2=rec['so2'], no2=rec['no2'], co=rec['co'], o3=rec['o3'],
                        primary_pollutant=rec['primary_pollutant'],
                        quality_level=rec['quality_level'],
                    ))
            if db_records:
                db.session.bulk_save_objects(db_records)
                db.session.commit()
                total += len(db_records)
            time.sleep(0.2)
        except Exception as e:
            print(f'  [AQI] {city.name} 跳过: {e}')
            continue

    print(f'[AQI] 自动补充完成: {total} 条')
    return total
