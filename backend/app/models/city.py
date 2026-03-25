from app import db
from datetime import datetime


class City(db.Model):
    """城市基础信息"""
    __tablename__ = 'cities'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='城市名称')
    province = db.Column(db.String(50), nullable=False, comment='所属省份')
    city_code = db.Column(db.String(20), nullable=False, unique=True, comment='城市编码')
    latitude = db.Column(db.Numeric(10, 6), nullable=False)
    longitude = db.Column(db.Numeric(10, 6), nullable=False)
    population = db.Column(db.Integer, comment='常住人口(万)')
    city_level = db.Column(db.Enum('一线', '新一线', '二线', '三线', '其他'), default='其他')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系
    stations = db.relationship('MonitoringStation', backref='city', lazy='dynamic')
    records = db.relationship('AirQualityRecord', backref='city', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'province': self.province,
            'cityCode': self.city_code,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'population': self.population,
            'cityLevel': self.city_level,
        }
