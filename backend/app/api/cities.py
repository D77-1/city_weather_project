"""城市相关 API"""
from flask import request
from app.api import api_bp
from app.models import City, MonitoringStation
from app.utils.response import success, error


@api_bp.route('/cities', methods=['GET'])
def get_cities():
    """获取城市列表，支持 ?province=xxx 筛选"""
    province = request.args.get('province')
    query = City.query
    if province:
        query = query.filter(City.province == province)
    cities = query.order_by(City.id).all()
    return success([c.to_dict() for c in cities])


@api_bp.route('/cities/<int:city_id>', methods=['GET'])
def get_city(city_id):
    """获取单个城市详情（含站点列表）"""
    city = City.query.get(city_id)
    if not city:
        return error('城市不存在', 404)
    data = city.to_dict()
    data['stations'] = [s.to_dict() for s in city.stations.filter_by(status='active').all()]
    return success(data)


@api_bp.route('/cities/<int:city_id>/stations', methods=['GET'])
def get_city_stations(city_id):
    """获取指定城市的所有监测站点"""
    city = City.query.get(city_id)
    if not city:
        return error('城市不存在', 404)
    stations = MonitoringStation.query.filter_by(city_id=city_id).all()
    return success([s.to_dict() for s in stations])


@api_bp.route('/provinces', methods=['GET'])
def get_provinces():
    """获取所有省份列表（去重）"""
    rows = City.query.with_entities(City.province).distinct().order_by(City.province).all()
    return success([r[0] for r in rows])
