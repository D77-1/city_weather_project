from app import db
from datetime import datetime


class AnomalyEvent(db.Model):
    """IQR 异常事件"""
    __tablename__ = 'anomaly_events'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id', ondelete='CASCADE'), nullable=False)
    station_id = db.Column(db.Integer, db.ForeignKey('monitoring_stations.id', ondelete='SET NULL'), nullable=True)
    metric_name = db.Column(db.String(20), nullable=False)
    record_time = db.Column(db.DateTime, nullable=False)
    actual_value = db.Column(db.Numeric(10, 2), nullable=False)
    q1_value = db.Column(db.Numeric(10, 2), nullable=False)
    q3_value = db.Column(db.Numeric(10, 2), nullable=False)
    iqr_value = db.Column(db.Numeric(10, 2), nullable=False)
    lower_bound = db.Column(db.Numeric(10, 2), nullable=False)
    upper_bound = db.Column(db.Numeric(10, 2), nullable=False)
    anomaly_type = db.Column(db.Enum('high', 'low'), nullable=False)
    severity = db.Column(db.Enum('mild', 'moderate', 'severe'), default='mild')
    status = db.Column(db.Enum('pending', 'confirmed', 'dismissed'), default='pending')
    description = db.Column(db.Text)
    ai_analysis = db.Column(db.Text, comment='AI 归因分析结果')
    created_at = db.Column(db.DateTime, default=datetime.now)

    city = db.relationship('City', backref=db.backref('anomalies', lazy='dynamic'))
    station = db.relationship('MonitoringStation', backref=db.backref('anomalies', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'cityId': self.city_id,
            'stationId': self.station_id,
            'metricName': self.metric_name,
            'recordTime': self.record_time.strftime('%Y-%m-%d %H:%M:%S'),
            'actualValue': float(self.actual_value),
            'q1': float(self.q1_value),
            'q3': float(self.q3_value),
            'iqr': float(self.iqr_value),
            'lowerBound': float(self.lower_bound),
            'upperBound': float(self.upper_bound),
            'anomalyType': self.anomaly_type,
            'severity': self.severity,
            'status': self.status,
            'description': self.description,
            'aiAnalysis': self.ai_analysis,
        }
