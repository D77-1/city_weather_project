"""
模拟数据生成器 - 生成符合真实分布的空气质量假数据
用于开发阶段替代真实 API 数据
"""
import math
import random
from datetime import datetime, timedelta
from app import db
from app.models import City, MonitoringStation, AirQualityRecord

# ---------- 城市种子数据（20个主要城市）----------
CITY_SEEDS = [
    {'name': '北京', 'province': '北京市', 'code': '110000', 'lat': 39.9042, 'lng': 116.4074, 'pop': 2189, 'level': '一线'},
    {'name': '上海', 'province': '上海市', 'code': '310000', 'lat': 31.2304, 'lng': 121.4737, 'pop': 2487, 'level': '一线'},
    {'name': '广州', 'province': '广东省', 'code': '440100', 'lat': 23.1291, 'lng': 113.2644, 'pop': 1881, 'level': '一线'},
    {'name': '深圳', 'province': '广东省', 'code': '440300', 'lat': 22.5431, 'lng': 114.0579, 'pop': 1768, 'level': '一线'},
    {'name': '成都', 'province': '四川省', 'code': '510100', 'lat': 30.5728, 'lng': 104.0668, 'pop': 2119, 'level': '新一线'},
    {'name': '杭州', 'province': '浙江省', 'code': '330100', 'lat': 30.2741, 'lng': 120.1551, 'pop': 1237, 'level': '新一线'},
    {'name': '武汉', 'province': '湖北省', 'code': '420100', 'lat': 30.5928, 'lng': 114.3055, 'pop': 1374, 'level': '新一线'},
    {'name': '南京', 'province': '江苏省', 'code': '320100', 'lat': 32.0603, 'lng': 118.7969, 'pop': 942, 'level': '新一线'},
    {'name': '重庆', 'province': '重庆市', 'code': '500000', 'lat': 29.5630, 'lng': 106.5516, 'pop': 3212, 'level': '新一线'},
    {'name': '天津', 'province': '天津市', 'code': '120000', 'lat': 39.0842, 'lng': 117.2010, 'pop': 1387, 'level': '新一线'},
    {'name': '西安', 'province': '陕西省', 'code': '610100', 'lat': 34.3416, 'lng': 108.9398, 'pop': 1295, 'level': '新一线'},
    {'name': '苏州', 'province': '江苏省', 'code': '320500', 'lat': 31.2990, 'lng': 120.5853, 'pop': 1275, 'level': '新一线'},
    {'name': '郑州', 'province': '河南省', 'code': '410100', 'lat': 34.7466, 'lng': 113.6254, 'pop': 1260, 'level': '新一线'},
    {'name': '长沙', 'province': '湖南省', 'code': '430100', 'lat': 28.2282, 'lng': 112.9388, 'pop': 1024, 'level': '新一线'},
    {'name': '沈阳', 'province': '辽宁省', 'code': '210100', 'lat': 41.8057, 'lng': 123.4315, 'pop': 911, 'level': '二线'},
    {'name': '哈尔滨', 'province': '黑龙江省', 'code': '230100', 'lat': 45.8038, 'lng': 126.5350, 'pop': 1001, 'level': '二线'},
    {'name': '昆明', 'province': '云南省', 'code': '530100', 'lat': 25.0389, 'lng': 102.7183, 'pop': 846, 'level': '二线'},
    {'name': '大连', 'province': '辽宁省', 'code': '210200', 'lat': 38.9140, 'lng': 121.6147, 'pop': 745, 'level': '二线'},
    {'name': '厦门', 'province': '福建省', 'code': '350200', 'lat': 24.4798, 'lng': 118.0894, 'pop': 528, 'level': '二线'},
    {'name': '海口', 'province': '海南省', 'code': '460100', 'lat': 20.0440, 'lng': 110.1999, 'pop': 287, 'level': '三线'},
]

# 每个城市的站点模板（随机选取 2~4 个）
STATION_TEMPLATES = ['城区站', '工业区站', '交通站', '郊区站', '背景站', '居民区站']

# 各城市空气质量基线（北方冬季偏高，南方沿海偏低）
# 字典键为城市名，值为 (aqi_base, seasonal_amplitude)
CITY_AQI_PROFILE = {
    '北京': (95, 55), '天津': (90, 50), '郑州': (88, 48), '西安': (85, 50),
    '沈阳': (82, 52), '哈尔滨': (80, 58), '武汉': (72, 35), '成都': (78, 38),
    '重庆': (75, 32), '长沙': (68, 30), '南京': (65, 28), '上海': (62, 25),
    '杭州': (60, 25), '苏州': (58, 22), '广州': (55, 20), '深圳': (48, 18),
    '厦门': (42, 15), '昆明': (38, 12), '大连': (50, 28), '海口': (32, 10),
}

QUALITY_LEVELS = [
    (0, 50, '优'), (51, 100, '良'), (101, 150, '轻度污染'),
    (151, 200, '中度污染'), (201, 300, '重度污染'), (301, 500, '严重污染'),
]

# 各城市气候基线: (年均温℃, 温差振幅, 年均湿度%, 年均降雨mm/日)
# 北方城市冬冷夏热、湿度低; 南方湿度高、降水多
CITY_WEATHER_PROFILE = {
    '北京': (13, 18, 52, 1.6), '天津': (13, 17, 58, 1.5), '郑州': (15, 16, 60, 1.8),
    '西安': (14, 17, 58, 1.5), '沈阳': (8, 22, 60, 1.8), '哈尔滨': (5, 25, 62, 1.6),
    '武汉': (17, 14, 72, 3.5), '成都': (17, 10, 78, 3.0), '重庆': (18, 10, 76, 3.2),
    '长沙': (18, 14, 74, 3.8), '南京': (16, 15, 72, 3.0), '上海': (17, 14, 70, 3.2),
    '杭州': (17, 14, 72, 3.8), '苏州': (16, 14, 70, 3.0), '广州': (22, 8, 76, 4.5),
    '深圳': (23, 7, 74, 4.8), '厦门': (21, 8, 72, 3.5), '昆明': (16, 5, 68, 2.5),
    '大连': (11, 16, 64, 2.0), '海口': (25, 5, 80, 5.0),
}

WIND_DIRECTIONS = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
WEATHER_CONDITIONS = {
    'dry':  ['晴', '晴', '晴', '多云', '多云', '阴'],
    'wet':  ['多云', '阴', '阴', '小雨', '小雨', '中雨'],
    'rainy': ['小雨', '中雨', '中雨', '大雨', '大雨', '暴雨'],
}


def _aqi_to_level(aqi):
    """AQI 数值转等级"""
    for low, high, level in QUALITY_LEVELS:
        if low <= aqi <= high:
            return level
    return '严重污染'


def _determine_primary_pollutant(pm25, pm10, so2, no2, co, o3):
    """判定首要污染物"""
    pollutants = {'PM2.5': pm25, 'PM10': pm10, 'SO2': so2, 'NO2': no2, 'CO': co, 'O3': o3}
    return max(pollutants, key=pollutants.get)


def _generate_daily_record(base_aqi, amplitude, day_of_year, noise_scale=1.0):
    """
    基于正弦季节模型 + 随机噪声生成单日数据
    冬季(day ~0, ~365) AQI 高，夏季(day ~182) AQI 低
    """
    seasonal = amplitude * math.cos(2 * math.pi * (day_of_year - 15) / 365)
    daily_noise = random.gauss(0, 12 * noise_scale)
    aqi = max(10, min(480, int(base_aqi + seasonal + daily_noise)))

    # 各污染物与 AQI 的经验相关系数
    pm25 = round(max(2, aqi * random.uniform(0.55, 0.72) + random.gauss(0, 5)), 1)
    pm10 = round(max(5, pm25 * random.uniform(1.3, 1.8) + random.gauss(0, 8)), 1)
    so2 = round(max(1, aqi * random.uniform(0.06, 0.12) + random.gauss(0, 2)), 1)
    no2 = round(max(3, aqi * random.uniform(0.20, 0.35) + random.gauss(0, 4)), 1)
    co = round(max(0.2, aqi * random.uniform(0.008, 0.015) + random.gauss(0, 0.1)), 2)
    o3 = round(max(5, (180 - aqi) * random.uniform(0.4, 0.7) + random.gauss(0, 10)), 1)

    primary = _determine_primary_pollutant(pm25, pm10, so2, no2, co, o3)
    level = _aqi_to_level(aqi)

    return aqi, pm25, pm10, so2, no2, co, o3, primary, level


def _generate_weather(city_name, day_of_year):
    """基于城市气候基线 + 季节正弦模型生成天气数据"""
    profile = CITY_WEATHER_PROFILE.get(city_name, (16, 12, 65, 2.5))
    avg_temp, temp_amp, avg_hum, avg_rain = profile

    # 温度: 夏高冬低 (day ~182 最高)
    temp = avg_temp + temp_amp * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    temp = round(temp + random.gauss(0, 2.5), 1)

    # 湿度: 夏季偏高
    humidity = int(avg_hum + 12 * math.sin(2 * math.pi * (day_of_year - 60) / 365) + random.gauss(0, 8))
    humidity = max(15, min(99, humidity))

    # 风速: 春季偏大
    wind_speed = round(max(0.2, 2.5 + 1.5 * math.sin(2 * math.pi * (day_of_year - 30) / 365) + random.gauss(0, 1.2)), 1)
    wind_dir = random.choice(WIND_DIRECTIONS)

    # 降水: 夏季概率高, 冬季低
    rain_prob = 0.15 + 0.3 * math.sin(2 * math.pi * (day_of_year - 60) / 365)
    if random.random() < max(0.05, rain_prob):
        rainfall = round(max(0.1, avg_rain * random.uniform(0.2, 3.0)), 1)
    else:
        rainfall = 0

    # 天气状况
    if rainfall > 10:
        weather = random.choice(WEATHER_CONDITIONS['rainy'])
    elif rainfall > 0:
        weather = random.choice(WEATHER_CONDITIONS['wet'])
    else:
        weather = random.choice(WEATHER_CONDITIONS['dry'])
    # 冬季低温可能降雪
    if temp < 2 and rainfall > 0:
        weather = random.choice(['小雪', '中雪', '雨夹雪'])

    return temp, humidity, wind_speed, wind_dir, rainfall, weather


def seed_cities():
    """插入城市种子数据，返回 {city_name: city_obj}"""
    cities = {}
    for s in CITY_SEEDS:
        city = City(
            name=s['name'], province=s['province'], city_code=s['code'],
            latitude=s['lat'], longitude=s['lng'],
            population=s['pop'], city_level=s['level'],
        )
        db.session.add(city)
        cities[s['name']] = city
    db.session.flush()  # 分配 ID
    return cities


def seed_stations(cities):
    """为每个城市生成 2~4 个监测站点"""
    stations = []
    for city_name, city in cities.items():
        num = random.randint(2, 4)
        chosen = random.sample(STATION_TEMPLATES, num)
        for i, tmpl in enumerate(chosen, 1):
            station = MonitoringStation(
                city_id=city.id,
                station_name=f'{city_name}{tmpl}',
                station_code=f'{city.city_code[:4]}A{i:03d}',
                address=f'{city_name}市{tmpl}监测点',
                latitude=float(city.latitude) + random.uniform(-0.05, 0.05),
                longitude=float(city.longitude) + random.uniform(-0.05, 0.05),
                station_type=random.choice(['国控', '省控', '市控']),
                status='active',
            )
            db.session.add(station)
            stations.append((city, station))
    db.session.flush()
    return stations


def seed_air_quality_records(stations, days=365):
    """
    为每个站点生成 N 天的日均数据
    默认 365 天（从今天往前推）
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total = 0

    for city, station in stations:
        profile = CITY_AQI_PROFILE.get(city.name, (60, 25))
        base_aqi, amplitude = profile
        # 每个站点加一点偏移，模拟站点差异
        station_offset = random.uniform(-8, 8)

        records = []
        for d in range(days):
            record_date = today - timedelta(days=days - d)
            day_of_year = record_date.timetuple().tm_yday

            aqi, pm25, pm10, so2, no2, co, o3, primary, level = _generate_daily_record(
                base_aqi + station_offset, amplitude, day_of_year
            )
            temp, hum, ws, wd, rain, weather = _generate_weather(city.name, day_of_year)

            records.append(AirQualityRecord(
                station_id=station.id,
                city_id=city.id,
                record_time=record_date,
                record_type='daily',
                aqi=aqi, pm25=pm25, pm10=pm10,
                so2=so2, no2=no2, co=co, o3=o3,
                temperature=temp, humidity=hum,
                wind_speed=ws, wind_direction=wd,
                rainfall=rain, weather_condition=weather,
                primary_pollutant=primary,
                quality_level=level,
            ))

        db.session.bulk_save_objects(records)
        total += len(records)

    db.session.commit()
    return total


def refresh_records():
    """
    将现有 mock 数据续期到今天：
    1. 找到数据库中最新记录日期
    2. 从最新日期的下一天开始，生成到今天的数据
    3. 注入约 10% 的「城市级」异常天（同城所有站点同日突变），让 IQR 检测能发现
    """
    from sqlalchemy import func
    latest = db.session.query(func.max(AirQualityRecord.record_time)).scalar()
    if not latest:
        print('[Mock] 数据库为空，请先执行 seed 命令')
        return 0

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_date = latest.replace(hour=0, minute=0, second=0, microsecond=0)
    gap_days = (today - last_date).days
    if gap_days <= 0:
        print('[Mock] 数据已是最新，无需刷新')
        return 0

    print(f'[Mock] 检测到数据缺口: {last_date.strftime("%Y-%m-%d")} → {today.strftime("%Y-%m-%d")} ({gap_days} 天)')

    # 按城市分组站点
    stations = db.session.query(
        MonitoringStation, City
    ).join(City, MonitoringStation.city_id == City.id).all()

    city_stations = {}
    for station, city in stations:
        city_stations.setdefault(city.id, (city, []))[1].append(station)

    total = 0
    for city_id, (city, city_stns) in city_stations.items():
        profile = CITY_AQI_PROFILE.get(city.name, (60, 25))
        base_aqi, amplitude = profile

        # 预先决定哪些天是该城市的异常天（约 10%，至少 1 天）
        spike_days = set()
        for d in range(1, gap_days + 1):
            if random.random() < 0.10:
                spike_days.add(d)
        if not spike_days and gap_days >= 1:
            spike_days.add(random.randint(1, gap_days))

        for station in city_stns:
            station_offset = random.uniform(-8, 8)
            records = []
            for d in range(1, gap_days + 1):
                record_date = last_date + timedelta(days=d)
                day_of_year = record_date.timetuple().tm_yday

                aqi, pm25, pm10, so2, no2, co, o3, primary, level = _generate_daily_record(
                    base_aqi + station_offset, amplitude, day_of_year
                )

                # 城市级异常天：所有站点同日异常
                if d in spike_days:
                    spike = random.choice([1.8, 2.0, 2.2, 0.25, 0.3])
                    aqi = max(10, min(480, int(aqi * spike)))
                    pm25 = round(max(1, pm25 * spike), 1)
                    pm10 = round(max(1, pm10 * spike), 1)
                    primary = _determine_primary_pollutant(pm25, pm10, so2, no2, co, o3)
                    level = _aqi_to_level(aqi)

                temp, hum, ws, wd, rain, weather = _generate_weather(city.name, day_of_year)

                records.append(AirQualityRecord(
                    station_id=station.id,
                    city_id=city.id,
                    record_time=record_date,
                    record_type='daily',
                    aqi=aqi, pm25=pm25, pm10=pm10,
                    so2=so2, no2=no2, co=co, o3=o3,
                    temperature=temp, humidity=hum,
                    wind_speed=ws, wind_direction=wd,
                    rainfall=rain, weather_condition=weather,
                    primary_pollutant=primary,
                    quality_level=level,
                ))

            db.session.bulk_save_objects(records)
            total += len(records)

    db.session.commit()
    print(f'[Mock] 已补充 {total} 条记录（{gap_days} 天 × {len(stations)} 站点）')
    return total


def seed_all(days=365):
    """一键生成全部模拟数据"""
    print('[Mock] 开始生成模拟数据...')
    cities = seed_cities()
    print(f'[Mock] 已创建 {len(cities)} 个城市')

    stations = seed_stations(cities)
    print(f'[Mock] 已创建 {len(stations)} 个监测站点')

    total = seed_air_quality_records(stations, days=days)
    print(f'[Mock] 已生成 {total} 条空气质量记录（{days}天 × {len(stations)}站点）')

    print('[Mock] 模拟数据生成完毕!')
    return {'cities': len(cities), 'stations': len(stations), 'records': total}
