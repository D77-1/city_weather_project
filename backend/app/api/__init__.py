from flask import Blueprint

api_bp = Blueprint('api', __name__)

from app.api import cities, air_quality, prediction, anomaly, ai_advice, weather  # noqa: F401, E402
