from app import db
from datetime import datetime


class AirQualityRecord(db.Model):
    """空气质量数据记录"""
    __tablename__ = 'air_quality_records'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id', ondelete='CASCADE'), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id', ondelete='CASCADE'), nullable=False)
    record_time = db.Column(db.DateTime, nullable=False, comment='监测时间')
    record_type = db.Column(db.Enum('hourly', 'daily'), default='daily')
    aqi = db.Column(db.SmallInteger, comment='空气质量指数')
    pm25 = db.Column(db.Numeric(8, 2), comment='PM2.5(ug/m3)')
    pm10 = db.Column(db.Numeric(8, 2), comment='PM10(ug/m3)')
    so2 = db.Column(db.Numeric(8, 2), comment='SO2(ug/m3)')
    no2 = db.Column(db.Numeric(8, 2), comment='NO2(ug/m3)')
    co = db.Column(db.Numeric(8, 2), comment='CO(mg/m3)')
    o3 = db.Column(db.Numeric(8, 2), comment='O3(ug/m3)')
    temperature = db.Column(db.Numeric(5, 1), comment='温度(℃)')
    humidity = db.Column(db.SmallInteger, comment='相对湿度(%)')
    wind_speed = db.Column(db.Numeric(5, 1), comment='风速(m/s)')
    wind_direction = db.Column(db.String(10), comment='风向')
    rainfall = db.Column(db.Numeric(6, 1), default=0, comment='降水量(mm)')
    weather_condition = db.Column(db.String(20), comment='天气状况')
    primary_pollutant = db.Column(db.String(20), comment='首要污染物')
    quality_level = db.Column(
        db.Enum('优', '良', '轻度污染', '中度污染', '重度污染', '严重污染'),
        comment='空气质量等级'
    )
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.Index('idx_city_time', 'city_id', 'record_time'),
        db.Index('idx_station_time', 'station_id', 'record_time'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'stationId': self.station_id,
            'cityId': self.city_id,
            'recordTime': self.record_time.strftime('%Y-%m-%d %H:%M:%S'),
            'recordType': self.record_type,
            'aqi': self.aqi,
            'pm25': float(self.pm25) if self.pm25 else None,
            'pm10': float(self.pm10) if self.pm10 else None,
            'so2': float(self.so2) if self.so2 else None,
            'no2': float(self.no2) if self.no2 else None,
            'co': float(self.co) if self.co else None,
            'o3': float(self.o3) if self.o3 else None,
            'temperature': float(self.temperature) if self.temperature else None,
            'humidity': int(self.humidity) if self.humidity else None,
            'windSpeed': float(self.wind_speed) if self.wind_speed else None,
            'windDirection': self.wind_direction,
            'rainfall': float(self.rainfall) if self.rainfall else 0,
            'weatherCondition': self.weather_condition,
            'primaryPollutant': self.primary_pollutant,
            'qualityLevel': self.quality_level,
        }
