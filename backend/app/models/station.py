from app import db
from datetime import datetime


class MonitoringStation(db.Model):
    """监测站点"""
    __tablename__ = 'monitoring_stations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id', ondelete='CASCADE'), nullable=False)
    station_name = db.Column(db.String(100), nullable=False, comment='站点名称')
    station_code = db.Column(db.String(30), nullable=False, unique=True, comment='站点编码')
    address = db.Column(db.String(255), comment='站点地址')
    latitude = db.Column(db.Numeric(10, 6), nullable=False)
    longitude = db.Column(db.Numeric(10, 6), nullable=False)
    station_type = db.Column(db.Enum('国控', '省控', '市控'), default='国控')
    status = db.Column(db.Enum('active', 'inactive', 'maintenance'), default='active')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    records = db.relationship('AirQualityRecord', backref='station', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'cityId': self.city_id,
            'stationName': self.station_name,
            'stationCode': self.station_code,
            'address': self.address,
            'latitude': float(self.latitude),
            'longitude': float(self.longitude),
            'stationType': self.station_type,
            'status': self.status,
        }
