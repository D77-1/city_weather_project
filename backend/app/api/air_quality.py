"""空气质量数据 API"""
from datetime import datetime, timedelta
from flask import request
from sqlalchemy import func, desc
from app.api import api_bp
from app import db
from app.models import AirQualityRecord, City
from app.utils.response import success, error


@api_bp.route('/air-quality/latest', methods=['GET'])
def get_latest_air_quality():
    """
    获取各城市最新一天的空气质量数据（城市级聚合均值）
    返回值按 AQI 降序排列
    """
    # 子查询: 找到最新的记录日期
    latest_date_sub = db.session.query(
        func.max(AirQualityRecord.record_time)
    ).scalar()

    if not latest_date_sub:
        return success([])

    # 按城市聚合最新一天的各站点平均值
    rows = db.session.query(
        AirQualityRecord.city_id,
        City.name.label('city_name'),
        City.province,
        func.round(func.avg(AirQualityRecord.aqi), 0).label('aqi'),
        func.round(func.avg(AirQualityRecord.pm25), 1).label('pm25'),
        func.round(func.avg(AirQualityRecord.pm10), 1).label('pm10'),
        func.round(func.avg(AirQualityRecord.so2), 1).label('so2'),
        func.round(func.avg(AirQualityRecord.no2), 1).label('no2'),
        func.round(func.avg(AirQualityRecord.co), 2).label('co'),
        func.round(func.avg(AirQualityRecord.o3), 1).label('o3'),
        func.round(func.avg(AirQualityRecord.temperature), 1).label('temperature'),
        func.round(func.avg(AirQualityRecord.humidity), 0).label('humidity'),
        func.round(func.avg(AirQualityRecord.wind_speed), 1).label('wind_speed'),
        func.round(func.avg(AirQualityRecord.rainfall), 1).label('rainfall'),
    ).join(City, AirQualityRecord.city_id == City.id) \
     .filter(AirQualityRecord.record_time == latest_date_sub) \
     .group_by(AirQualityRecord.city_id, City.name, City.province) \
     .order_by(desc('aqi')) \
     .all()

    # 获取每个城市的一条记录用于读取非聚合字段(风向、天气)
    weather_detail = {}
    detail_rows = AirQualityRecord.query.filter(
        AirQualityRecord.record_time == latest_date_sub
    ).all()
    for dr in detail_rows:
        if dr.city_id not in weather_detail:
            weather_detail[dr.city_id] = dr

    data = []
    for r in rows:
        aqi_val = int(r.aqi) if r.aqi else 0
        wd = weather_detail.get(r.city_id)
        data.append({
            'cityId': r.city_id,
            'cityName': r.city_name,
            'province': r.province,
            'aqi': aqi_val,
            'pm25': float(r.pm25) if r.pm25 else 0,
            'pm10': float(r.pm10) if r.pm10 else 0,
            'so2': float(r.so2) if r.so2 else 0,
            'no2': float(r.no2) if r.no2 else 0,
            'co': float(r.co) if r.co else 0,
            'o3': float(r.o3) if r.o3 else 0,
            'temperature': float(r.temperature) if r.temperature else None,
            'humidity': int(r.humidity) if r.humidity else None,
            'windSpeed': float(r.wind_speed) if r.wind_speed else None,
            'windDirection': wd.wind_direction if wd else None,
            'rainfall': float(r.rainfall) if r.rainfall else 0,
            'weatherCondition': wd.weather_condition if wd else None,
            'qualityLevel': _aqi_to_level(aqi_val),
            'recordDate': latest_date_sub.strftime('%Y-%m-%d'),
            'dataSource': 'local_db_daily_avg',
        })

    return success(data)


@api_bp.route('/air-quality/history', methods=['GET'])
def get_history():
    """
    获取某城市的历史空气质量趋势
    参数:
      city_id (必填): 城市ID
      days (选填): 天数，默认30
      metric (选填): 指标，默认 aqi
    返回: 按日期排列的时序数组
    """
    city_id = request.args.get('city_id', type=int)
    if not city_id:
        return error('缺少 city_id 参数')
    days = request.args.get('days', 30, type=int)
    days = min(days, 365)

    # 以 DB 中最新记录日期为基准（而非 datetime.now()），避免数据过期时查不到记录
    latest_date = db.session.query(func.max(AirQualityRecord.record_time)).filter(
        AirQualityRecord.city_id == city_id
    ).scalar()
    if not latest_date:
        return success([])
    start_date = latest_date - timedelta(days=days)

    # 按日聚合（一个城市多个站点取均值）
    rows = db.session.query(
        func.date(AirQualityRecord.record_time).label('date'),
        func.round(func.avg(AirQualityRecord.aqi), 0).label('aqi'),
        func.round(func.avg(AirQualityRecord.pm25), 1).label('pm25'),
        func.round(func.avg(AirQualityRecord.pm10), 1).label('pm10'),
        func.round(func.avg(AirQualityRecord.so2), 1).label('so2'),
        func.round(func.avg(AirQualityRecord.no2), 1).label('no2'),
        func.round(func.avg(AirQualityRecord.co), 2).label('co'),
        func.round(func.avg(AirQualityRecord.o3), 1).label('o3'),
        func.round(func.avg(AirQualityRecord.temperature), 1).label('temperature'),
        func.round(func.avg(AirQualityRecord.humidity), 0).label('humidity'),
        func.round(func.avg(AirQualityRecord.wind_speed), 1).label('wind_speed'),
        func.round(func.avg(AirQualityRecord.rainfall), 1).label('rainfall'),
    ).filter(
        AirQualityRecord.city_id == city_id,
        AirQualityRecord.record_time >= start_date,
    ).group_by(func.date(AirQualityRecord.record_time)) \
     .order_by('date') \
     .all()

    data = []
    for r in rows:
        data.append({
            'date': str(r.date),
            'aqi': int(r.aqi) if r.aqi else 0,
            'pm25': float(r.pm25) if r.pm25 else 0,
            'pm10': float(r.pm10) if r.pm10 else 0,
            'so2': float(r.so2) if r.so2 else 0,
            'no2': float(r.no2) if r.no2 else 0,
            'co': float(r.co) if r.co else 0,
            'o3': float(r.o3) if r.o3 else 0,
            'temperature': float(r.temperature) if r.temperature else None,
            'humidity': int(r.humidity) if r.humidity else None,
            'windSpeed': float(r.wind_speed) if r.wind_speed else None,
            'rainfall': float(r.rainfall) if r.rainfall else 0,
        })

    return success(data)


@api_bp.route('/air-quality/ranking', methods=['GET'])
def get_ranking():
    """
    城市 AQI 排名（最新一天）
    参数:
      order: asc(最优) / desc(最差), 默认 desc
      limit: 返回数量, 默认 10
    """
    order = request.args.get('order', 'desc')
    limit = request.args.get('limit', 10, type=int)
    limit = min(limit, 50)

    latest_date = db.session.query(
        func.max(AirQualityRecord.record_time)
    ).scalar()

    if not latest_date:
        return success([])

    avg_aqi = func.round(func.avg(AirQualityRecord.aqi), 0).label('avg_aqi')
    order_col = avg_aqi.asc() if order == 'asc' else avg_aqi.desc()

    rows = db.session.query(
        AirQualityRecord.city_id,
        City.name.label('city_name'),
        avg_aqi,
    ).join(City, AirQualityRecord.city_id == City.id) \
     .filter(AirQualityRecord.record_time == latest_date) \
     .group_by(AirQualityRecord.city_id, City.name) \
     .order_by(order_col) \
     .limit(limit) \
     .all()

    data = [{
        'rank': i + 1,
        'cityId': r.city_id,
        'cityName': r.city_name,
        'aqi': int(r.avg_aqi) if r.avg_aqi else 0,
        'qualityLevel': _aqi_to_level(int(r.avg_aqi) if r.avg_aqi else 0),
    } for i, r in enumerate(rows)]

    return success(data)


@api_bp.route('/air-quality/station/<int:station_id>', methods=['GET'])
def get_station_records(station_id):
    """
    获取指定站点的历史记录
    参数: days (默认30)
    """
    days = request.args.get('days', 30, type=int)
    start_date = datetime.now() - timedelta(days=days)

    records = AirQualityRecord.query.filter(
        AirQualityRecord.station_id == station_id,
        AirQualityRecord.record_time >= start_date,
    ).order_by(AirQualityRecord.record_time).all()

    return success([r.to_dict() for r in records])


@api_bp.route('/air-quality/map-data', methods=['GET'])
def get_map_data():
    """
    获取地图热力图数据: 每个城市最新 AQI + 坐标
    供 ECharts 中国地图散点/热力图使用
    """
    latest_date = db.session.query(
        func.max(AirQualityRecord.record_time)
    ).scalar()

    if not latest_date:
        return success([])

    rows = db.session.query(
        City.id,
        City.name,
        City.latitude,
        City.longitude,
        func.round(func.avg(AirQualityRecord.aqi), 0).label('aqi'),
    ).join(AirQualityRecord, City.id == AirQualityRecord.city_id) \
     .filter(AirQualityRecord.record_time == latest_date) \
     .group_by(City.id, City.name, City.latitude, City.longitude) \
     .all()

    data = [{
        'cityId': r.id,
        'name': r.name,
        'value': [float(r.longitude), float(r.latitude), int(r.aqi) if r.aqi else 0],
    } for r in rows]

    return success(data)


def _aqi_to_level(aqi):
    levels = [
        (0, 50, '优'), (51, 100, '良'), (101, 150, '轻度污染'),
        (151, 200, '中度污染'), (201, 300, '重度污染'), (301, 500, '严重污染'),
    ]
    for low, high, level in levels:
        if low <= aqi <= high:
            return level
    return '严重污染'
