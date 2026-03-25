from app import db
from datetime import datetime


class PredictionResult(db.Model):
    """移动平均预测结果"""
    __tablename__ = 'prediction_results'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id', ondelete='CASCADE'), nullable=False)
    algorithm_type = db.Column(db.String(30), nullable=False, default='moving_average')
    metric_name = db.Column(db.String(20), nullable=False, comment='指标名')
    prediction_date = db.Column(db.Date, nullable=False, comment='预测目标日期')
    predicted_value = db.Column(db.Numeric(10, 2), nullable=False)
    confidence_upper = db.Column(db.Numeric(10, 2), comment='置信上界')
    confidence_lower = db.Column(db.Numeric(10, 2), comment='置信下界')
    actual_value = db.Column(db.Numeric(10, 2), comment='实际值(回填)')
    window_size = db.Column(db.Integer, default=7, comment='窗口大小')
    mape = db.Column(db.Numeric(6, 2), comment='MAPE(%)')
    created_at = db.Column(db.DateTime, default=datetime.now)

    city = db.relationship('City', backref=db.backref('predictions', lazy='dynamic'))

    __table_args__ = (
        db.Index('idx_city_metric_date', 'city_id', 'metric_name', 'prediction_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'cityId': self.city_id,
            'algorithmType': self.algorithm_type,
            'metricName': self.metric_name,
            'predictionDate': self.prediction_date.strftime('%Y-%m-%d'),
            'predictedValue': float(self.predicted_value),
            'confidenceUpper': float(self.confidence_upper) if self.confidence_upper else None,
            'confidenceLower': float(self.confidence_lower) if self.confidence_lower else None,
            'actualValue': float(self.actual_value) if self.actual_value else None,
            'windowSize': self.window_size,
            'mape': float(self.mape) if self.mape else None,
        }
