"""天气 + 真实空气质量 API - 调用 Open-Meteo 获取真实数据"""
from flask import request
from app.api import api_bp
from app.models import City
from app.utils.response import success, error
from app.services.weather_service import (
    get_realtime_weather, get_weather_forecast, get_weather_history,
)
from app.services.real_aqi_service import (
    get_realtime_aqi, get_aqi_forecast, get_aqi_history,
)


def _get_city_or_error(city_id):
    city = City.query.get(city_id)
    if not city:
        return None, error(f'城市 {city_id} 不存在', 404)
    return city, None


@api_bp.route('/weather/realtime', methods=['GET'])
def weather_realtime():
    """获取某城市实时天气"""
    city_id = request.args.get('city_id', type=int)
    if not city_id:
        return error('缺少 city_id')
    city, err = _get_city_or_error(city_id)
    if err:
        return err
    data = get_realtime_weather(float(city.latitude), float(city.longitude))
    if not data:
        return error('天气服务暂时不可用')
    data['cityId'] = city.id
    data['cityName'] = city.name
    return success(data)


@api_bp.route('/weather/forecast', methods=['GET'])
def weather_forecast():
    """获取某城市未来 7~16 天预报"""
    city_id = request.args.get('city_id', type=int)
    days = request.args.get('days', 7, type=int)
    if not city_id:
        return error('缺少 city_id')
    city, err = _get_city_or_error(city_id)
    if err:
        return err
    data = get_weather_forecast(float(city.latitude), float(city.longitude), days)
    return success({
        'cityId': city.id,
        'cityName': city.name,
        'forecast': data,
    })


@api_bp.route('/weather/history', methods=['GET'])
def weather_history():
    """获取某城市过去 N 天历史天气"""
    city_id = request.args.get('city_id', type=int)
    days = request.args.get('days', 30, type=int)
    if not city_id:
        return error('缺少 city_id')
    city, err = _get_city_or_error(city_id)
    if err:
        return err
    data = get_weather_history(float(city.latitude), float(city.longitude), days)
    return success({
        'cityId': city.id,
        'cityName': city.name,
        'history': data,
    })


@api_bp.route('/realtime-aqi', methods=['GET'])
def realtime_aqi():
    """获取某城市真实实时空气质量 (Open-Meteo CAMS)"""
    city_id = request.args.get('city_id', type=int)
    if not city_id:
        return error('缺少 city_id')
    city, err = _get_city_or_error(city_id)
    if err:
        return err
    data = get_realtime_aqi(float(city.latitude), float(city.longitude))
    if not data:
        return error('空气质量服务暂时不可用')
    data['cityId'] = city.id
    data['cityName'] = city.name
    return success(data)


@api_bp.route('/realtime-all', methods=['GET'])
def realtime_all():
    """获取某城市 天气+AQI 合并的实时数据"""
    city_id = request.args.get('city_id', type=int)
    if not city_id:
        return error('缺少 city_id')
    city, err = _get_city_or_error(city_id)
    if err:
        return err
    lat, lng = float(city.latitude), float(city.longitude)
    weather = get_realtime_weather(lat, lng) or {}
    aqi = get_realtime_aqi(lat, lng) or {}
    return success({
        'cityId': city.id,
        'cityName': city.name,
        'weather': weather,
        'airQuality': aqi,
        'source': 'Open-Meteo (实时真实数据)',
    })


@api_bp.route('/aqi-forecast', methods=['GET'])
def aqi_forecast():
    """获取某城市未来5天 AQI 预报 (真实数据)"""
    city_id = request.args.get('city_id', type=int)
    days = request.args.get('days', 5, type=int)
    if not city_id:
        return error('缺少 city_id')
    city, err = _get_city_or_error(city_id)
    if err:
        return err
    data = get_aqi_forecast(float(city.latitude), float(city.longitude), days)
    return success({
        'cityId': city.id,
        'cityName': city.name,
        'forecast': data,
        'source': 'Open-Meteo CAMS (真实预报)',
    })


@api_bp.route('/aqi-history-real', methods=['GET'])
def aqi_history_real():
    """获取某城市过去N天真实AQI历史 (Open-Meteo)"""
    city_id = request.args.get('city_id', type=int)
    days = request.args.get('days', 30, type=int)
    if not city_id:
        return error('缺少 city_id')
    city, err = _get_city_or_error(city_id)
    if err:
        return err
    data = get_aqi_history(float(city.latitude), float(city.longitude), days)
    return success({
        'cityId': city.id,
        'cityName': city.name,
        'history': data,
        'source': 'Open-Meteo CAMS (真实历史)',
    })


@api_bp.route('/compare', methods=['GET'])
def compare_cities():
    """
    多城市对比数据
    参数: city_ids=1,2,3 (逗号分隔)
    """
    ids_str = request.args.get('city_ids', '')
    if not ids_str:
        return error('缺少 city_ids 参数')
    try:
        city_ids = [int(x) for x in ids_str.split(',')]
    except ValueError:
        return error('city_ids 格式错误')

    from sqlalchemy import func
    from app import db
    from app.models import AirQualityRecord

    latest_date = db.session.query(func.max(AirQualityRecord.record_time)).scalar()
    if not latest_date:
        return success([])

    results = []
    for cid in city_ids[:5]:  # 最多5个城市
        city = City.query.get(cid)
        if not city:
            continue

        # 最新AQI
        row = db.session.query(
            func.round(func.avg(AirQualityRecord.aqi), 0).label('aqi'),
            func.round(func.avg(AirQualityRecord.pm25), 1).label('pm25'),
            func.round(func.avg(AirQualityRecord.pm10), 1).label('pm10'),
            func.round(func.avg(AirQualityRecord.so2), 1).label('so2'),
            func.round(func.avg(AirQualityRecord.no2), 1).label('no2'),
            func.round(func.avg(AirQualityRecord.co), 2).label('co'),
            func.round(func.avg(AirQualityRecord.o3), 1).label('o3'),
        ).filter(
            AirQualityRecord.city_id == cid,
            AirQualityRecord.record_time == latest_date,
        ).first()

        # 30天历史
        start = latest_date - __import__('datetime').timedelta(days=30)
        history = db.session.query(
            func.date(AirQualityRecord.record_time).label('date'),
            func.round(func.avg(AirQualityRecord.aqi), 0).label('aqi'),
        ).filter(
            AirQualityRecord.city_id == cid,
            AirQualityRecord.record_time >= start,
        ).group_by(func.date(AirQualityRecord.record_time)).order_by('date').all()

        # 实时天气
        weather = get_realtime_weather(float(city.latitude), float(city.longitude))

        results.append({
            'cityId': city.id,
            'cityName': city.name,
            'province': city.province,
            'aqi': int(row.aqi) if row and row.aqi else 0,
            'pm25': float(row.pm25) if row and row.pm25 else 0,
            'pm10': float(row.pm10) if row and row.pm10 else 0,
            'so2': float(row.so2) if row and row.so2 else 0,
            'no2': float(row.no2) if row and row.no2 else 0,
            'co': float(row.co) if row and row.co else 0,
            'o3': float(row.o3) if row and row.o3 else 0,
            'weather': weather,
            'history': [{'date': str(h.date), 'aqi': int(h.aqi)} for h in history],
        })

    return success(results)
