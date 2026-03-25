"""
真实数据导入工具
用法:
  python import_real_data.py data.csv
  python import_real_data.py --dir ./csv_files/     (批量导入目录下所有csv)

CSV 格式要求 (列名不区分大小写, 支持中英文列名):
  date,city,aqi,pm2.5,pm10,so2,no2,co,o3,quality_level,primary_pollutant

示例行:
  2025-01-01,北京,156,120.5,189.3,15.2,68.4,1.8,45.0,中度污染,PM2.5
"""
import sys
import os
import csv
import glob
from datetime import datetime

# 把项目根目录加入 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import City, MonitoringStation, AirQualityRecord

# ===== 列名映射（支持多种写法） =====
COL_MAP = {
    # date
    'date': 'date', '日期': 'date', 'datetime': 'date', '监测时间': 'date', 'time': 'date',
    # city
    'city': 'city', '城市': 'city', '地区': 'city', 'area': 'city', '城市名称': 'city', '地点': 'city',
    # aqi
    'aqi': 'aqi', '空气质量指数': 'aqi', 'AQI': 'aqi',
    # pm2.5
    'pm2.5': 'pm25', 'pm25': 'pm25', 'PM2.5': 'pm25', 'pm2.5_24h': 'pm25',
    'PM2.5_24h': 'pm25', 'PM2.5浓度': 'pm25',
    # pm10
    'pm10': 'pm10', 'PM10': 'pm10', 'pm10_24h': 'pm10', 'PM10_24h': 'pm10', 'PM10浓度': 'pm10',
    # so2
    'so2': 'so2', 'SO2': 'so2', 'so2_24h': 'so2', 'SO2浓度': 'so2',
    # no2
    'no2': 'no2', 'NO2': 'no2', 'no2_24h': 'no2', 'NO2浓度': 'no2',
    # co
    'co': 'co', 'CO': 'co', 'co_24h': 'co', 'CO浓度': 'co',
    # o3
    'o3': 'o3', 'O3': 'o3', 'o3_8h': 'o3', 'O3_8h': 'o3', 'o3_8h_24h': 'o3', 'O3浓度': 'o3',
    # quality
    'quality_level': 'quality', '质量等级': 'quality', '空气质量等级': 'quality',
    'quality': 'quality', 'AQI等级': 'quality', '等级': 'quality',
    # primary pollutant
    'primary_pollutant': 'primary', '首要污染物': 'primary', '主要污染物': 'primary',
}

# 城市经纬度（20个主要城市 + 备用）
CITY_GEO = {
    '北京': (39.9042, 116.4074, '北京市', '一线'),
    '上海': (31.2304, 121.4737, '上海市', '一线'),
    '广州': (23.1291, 113.2644, '广东省', '一线'),
    '深圳': (22.5431, 114.0579, '广东省', '一线'),
    '成都': (30.5728, 104.0668, '四川省', '新一线'),
    '杭州': (30.2741, 120.1551, '浙江省', '新一线'),
    '武汉': (30.5928, 114.3055, '湖北省', '新一线'),
    '南京': (32.0603, 118.7969, '江苏省', '新一线'),
    '重庆': (29.5630, 106.5516, '重庆市', '新一线'),
    '天津': (39.0842, 117.2010, '天津市', '新一线'),
    '西安': (34.3416, 108.9398, '陕西省', '新一线'),
    '苏州': (31.2990, 120.5853, '江苏省', '新一线'),
    '郑州': (34.7466, 113.6254, '河南省', '新一线'),
    '长沙': (28.2282, 112.9388, '湖南省', '新一线'),
    '沈阳': (41.8057, 123.4315, '辽宁省', '二线'),
    '哈尔滨': (45.8038, 126.5350, '黑龙江省', '二线'),
    '昆明': (25.0389, 102.7183, '云南省', '二线'),
    '大连': (38.9140, 121.6147, '辽宁省', '二线'),
    '厦门': (24.4798, 118.0894, '福建省', '二线'),
    '海口': (20.0440, 110.1999, '海南省', '三线'),
    '合肥': (31.8206, 117.2272, '安徽省', '二线'),
    '济南': (36.6512, 117.1201, '山东省', '二线'),
    '青岛': (36.0671, 120.3826, '山东省', '二线'),
    '南昌': (28.6820, 115.8579, '江西省', '二线'),
    '福州': (26.0745, 119.2965, '福建省', '二线'),
    '石家庄': (38.0428, 114.5149, '河北省', '二线'),
    '太原': (37.8706, 112.5489, '山西省', '二线'),
    '长春': (43.8171, 125.3235, '吉林省', '二线'),
    '贵阳': (26.6470, 106.6302, '贵州省', '二线'),
    '南宁': (22.8170, 108.3665, '广西壮族自治区', '二线'),
    '兰州': (36.0611, 103.8343, '甘肃省', '三线'),
    '乌鲁木齐': (43.7930, 87.6271, '新疆维吾尔自治区', '三线'),
    '拉萨': (29.6500, 91.1000, '西藏自治区', '其他'),
}

QUALITY_LEVELS = ['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染']


def aqi_to_level(aqi):
    if aqi is None: return None
    if aqi <= 50: return '优'
    if aqi <= 100: return '良'
    if aqi <= 150: return '轻度污染'
    if aqi <= 200: return '中度污染'
    if aqi <= 300: return '重度污染'
    return '严重污染'


def safe_float(val):
    if val is None or val == '' or val == '-' or val == 'NA' or val == 'NULL':
        return None
    try:
        v = float(str(val).strip())
        return v if v >= 0 else None
    except (ValueError, TypeError):
        return None


def safe_int(val):
    f = safe_float(val)
    return int(f) if f is not None else None


def normalize_columns(header):
    """将 CSV 列名标准化"""
    mapping = {}
    for i, col in enumerate(header):
        col_clean = col.strip().replace('\ufeff', '')  # 去 BOM
        if col_clean in COL_MAP:
            mapping[COL_MAP[col_clean]] = i
        elif col_clean.lower() in COL_MAP:
            mapping[COL_MAP[col_clean.lower()]] = i
    return mapping


def get_or_create_city(name):
    """获取或创建城市记录"""
    city = City.query.filter_by(name=name).first()
    if city:
        return city

    geo = CITY_GEO.get(name, (30.0, 110.0, '未知', '其他'))
    city = City(
        name=name,
        province=geo[2],
        city_code=str(hash(name) % 900000 + 100000),
        latitude=geo[0],
        longitude=geo[1],
        city_level=geo[3],
    )
    db.session.add(city)
    db.session.flush()
    return city


def get_or_create_station(city):
    """获取或创建该城市的默认站点"""
    station = MonitoringStation.query.filter_by(city_id=city.id).first()
    if station:
        return station

    station = MonitoringStation(
        city_id=city.id,
        station_name=f'{city.name}综合站',
        station_code=f'{city.city_code[:6]}A001',
        address=f'{city.name}市区',
        latitude=float(city.latitude),
        longitude=float(city.longitude),
        station_type='国控',
        status='active',
    )
    db.session.add(station)
    db.session.flush()
    return station


def import_csv(filepath):
    """导入单个 CSV 文件"""
    print(f'  读取: {filepath}')

    # 自动检测编码
    for encoding in ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'gb18030']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                f.read(1024)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    else:
        encoding = 'utf-8'

    with open(filepath, 'r', encoding=encoding) as f:
        reader = csv.reader(f)
        header = next(reader)
        col_map = normalize_columns(header)

        if 'date' not in col_map or 'city' not in col_map:
            print(f'  [跳过] 缺少必要列 date/city, 识别到的列: {list(col_map.keys())}')
            print(f'         原始列名: {header}')
            return 0

        print(f'  识别到的列: {list(col_map.keys())}')

        city_cache = {}     # name -> (city, station)
        records = []
        count = 0

        for row in reader:
            try:
                city_name = row[col_map['city']].strip()
                date_str = row[col_map['date']].strip()

                # 跳过空行
                if not city_name or not date_str:
                    continue

                # 解析日期（支持多种格式）
                record_time = None
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']:
                    try:
                        record_time = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                if not record_time:
                    continue

                # 获取/创建城市和站点
                if city_name not in city_cache:
                    city = get_or_create_city(city_name)
                    station = get_or_create_station(city)
                    city_cache[city_name] = (city, station)
                city, station = city_cache[city_name]

                aqi = safe_int(row[col_map['aqi']]) if 'aqi' in col_map else None
                pm25 = safe_float(row[col_map['pm25']]) if 'pm25' in col_map else None
                pm10 = safe_float(row[col_map['pm10']]) if 'pm10' in col_map else None
                so2 = safe_float(row[col_map['so2']]) if 'so2' in col_map else None
                no2 = safe_float(row[col_map['no2']]) if 'no2' in col_map else None
                co = safe_float(row[col_map['co']]) if 'co' in col_map else None
                o3 = safe_float(row[col_map['o3']]) if 'o3' in col_map else None

                quality = None
                if 'quality' in col_map:
                    q = row[col_map['quality']].strip()
                    if q in QUALITY_LEVELS:
                        quality = q
                if not quality and aqi is not None:
                    quality = aqi_to_level(aqi)

                primary = row[col_map['primary']].strip() if 'primary' in col_map else None

                records.append(AirQualityRecord(
                    station_id=station.id,
                    city_id=city.id,
                    record_time=record_time,
                    record_type='daily',
                    aqi=aqi, pm25=pm25, pm10=pm10,
                    so2=so2, no2=no2, co=co, o3=o3,
                    primary_pollutant=primary or None,
                    quality_level=quality,
                ))

                # 每 2000 条批量写入
                if len(records) >= 2000:
                    db.session.bulk_save_objects(records)
                    db.session.commit()
                    count += len(records)
                    print(f'    已导入 {count} 条...')
                    records = []

            except (IndexError, KeyError) as e:
                continue

        # 写入剩余
        if records:
            db.session.bulk_save_objects(records)
            db.session.commit()
            count += len(records)

        print(f'  完成: {count} 条记录, {len(city_cache)} 个城市')
        return count


def main():
    if len(sys.argv) < 2:
        print('用法:')
        print('  python import_real_data.py data.csv')
        print('  python import_real_data.py --dir ./csv_files/')
        print()
        print('CSV 列名示例 (顺序不限, 支持中英文):')
        print('  date, city, aqi, pm2.5, pm10, so2, no2, co, o3, quality_level, primary_pollutant')
        print('  日期, 城市, AQI, PM2.5, PM10, SO2, NO2, CO, O3, 质量等级, 首要污染物')
        sys.exit(1)

    app = create_app()

    with app.app_context():
        # 清空旧的空气质量数据（保留城市和站点表结构）
        old_count = AirQualityRecord.query.count()
        if old_count > 0:
            print(f'清空旧数据: {old_count} 条记录...')
            AirQualityRecord.query.delete()
            # 同时清空预测和异常结果（基于旧数据的）
            from app.models import PredictionResult, AnomalyEvent
            PredictionResult.query.delete()
            AnomalyEvent.query.delete()
            db.session.commit()

        total = 0

        if sys.argv[1] == '--dir':
            dir_path = sys.argv[2] if len(sys.argv) > 2 else '.'
            files = sorted(glob.glob(os.path.join(dir_path, '*.csv')))
            print(f'找到 {len(files)} 个 CSV 文件')
            for f in files:
                total += import_csv(f)
        else:
            for filepath in sys.argv[1:]:
                total += import_csv(filepath)

        cities = City.query.count()
        stations = MonitoringStation.query.count()
        print(f'\n===== 导入完成 =====')
        print(f'总记录: {total} 条')
        print(f'城市: {cities} 个')
        print(f'站点: {stations} 个')
        print(f'\n接下来可以运行预测和异常检测:')
        print(f'  D:/conda_envs/python3.12/python.exe -c "from app import create_app; ...')
        print(f'  或在 Flask shell 中: flask analyze')


if __name__ == '__main__':
    main()
