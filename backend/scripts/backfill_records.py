"""
数据补齐脚本
用途: 把所有"最新记录早于目标日期"的城市/站点,按各自最近 N 天的均值与波动,
      逐日生成 record 一直补到目标日期。每个站点单独建模,数值带轻度自相关
      与小幅扰动,确保不会偏离真实分布。

用法:
    python scripts/backfill_records.py 2026-05-09           # 干跑,只打印计划
    python scripts/backfill_records.py 2026-05-09 --apply   # 真正写入

约束:
- 只对那些站点最新 record_time < 目标日期的站点补记录,已有的不动
- 每条新记录由该站点过去 14 天数据生成基线和波动,clip 到 mean ± 1.5σ
- AQI / quality_level / primary_pollutant 用项目已有 HJ 633-2012 算法重算
"""
import os
import sys
import argparse
import random
from datetime import datetime, timedelta
from statistics import mean, stdev

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import City, MonitoringStation, AirQualityRecord
from app.services.aqi_service import _calc_cn_aqi, _aqi_to_level

LOOKBACK_DAYS = 14          # 用最近 14 天作基线
NOISE_SCALE = 0.04          # 单日相对扰动幅度 ±4%
AR_COEF = 0.65              # 新值 = AR_COEF*前一天 + (1-AR_COEF)*均值 + 噪声
CLIP_SIGMA = 1.5            # 数值 clip 在 mean ± 1.5σ

POLL_FIELDS = ['pm25', 'pm10', 'so2', 'no2', 'co', 'o3']
WEATHER_FIELDS = ['temperature', 'humidity', 'wind_speed', 'rainfall']


def _to_float(v):
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _stats(values):
    """返回 (mean, std),忽略 None;不足 2 个返回 std=0"""
    vals = [v for v in values if v is not None]
    if not vals:
        return None, 0.0
    m = mean(vals)
    s = stdev(vals) if len(vals) >= 2 else 0.0
    return m, s


def _next_value(prev, m, s, lo=0.0, rng=None):
    """AR(1)+噪声,clip 到 [max(lo, m-1.5σ), m+1.5σ]"""
    if m is None:
        return None
    r = rng or random
    base = AR_COEF * (prev if prev is not None else m) + (1 - AR_COEF) * m
    noise = base * r.uniform(-NOISE_SCALE, NOISE_SCALE)
    val = base + noise
    if s > 0:
        val = max(m - CLIP_SIGMA * s, min(m + CLIP_SIGMA * s, val))
    return max(lo, val)


def _round(field, val):
    if val is None:
        return None
    if field == 'co':
        return round(val, 2)
    if field in ('pm25', 'pm10', 'so2', 'no2', 'o3', 'temperature', 'wind_speed', 'rainfall'):
        return round(val, 1)
    if field == 'humidity':
        return int(round(val))
    return val


def _gather_station_baseline(station_id, ref_date):
    """取站点最新一条往前 LOOKBACK_DAYS 内的记录,返回各字段 (mean, std) + 最新一条"""
    last_dt = (db.session.query(db.func.max(AirQualityRecord.record_time))
               .filter(AirQualityRecord.station_id == station_id).scalar())
    if last_dt is None:
        return None, None
    start = last_dt - timedelta(days=LOOKBACK_DAYS)
    rows = (AirQualityRecord.query
            .filter(AirQualityRecord.station_id == station_id,
                    AirQualityRecord.record_time >= start,
                    AirQualityRecord.record_time <= last_dt)
            .order_by(AirQualityRecord.record_time.asc())
            .all())
    if not rows:
        return None, None

    stats = {}
    for f in POLL_FIELDS + WEATHER_FIELDS:
        vals = [_to_float(getattr(r, f)) for r in rows]
        stats[f] = _stats(vals)

    last = rows[-1]
    return stats, last


def backfill(target_date_str, apply_changes=False):
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d')

    # 找所有"站点最新 record_time < 目标日期"的站点
    stations = MonitoringStation.query.all()
    plan = []  # [(station, last_date, missing_dates)]
    for st in stations:
        last_dt = (db.session.query(db.func.max(AirQualityRecord.record_time))
                   .filter(AirQualityRecord.station_id == st.id).scalar())
        if last_dt is None:
            continue
        if last_dt >= target_date:
            continue
        # 生成缺失日期列表 (last+1 .. target)
        cur = last_dt + timedelta(days=1)
        missing = []
        while cur <= target_date:
            missing.append(cur)
            cur += timedelta(days=1)
        if missing:
            plan.append((st, last_dt, missing))

    # 按城市汇总打印
    by_city = {}
    for st, last_dt, missing in plan:
        c = City.query.get(st.city_id)
        by_city.setdefault(c.name, {'last': last_dt, 'stations': 0, 'days': len(missing)})
        by_city[c.name]['stations'] += 1
        if last_dt < by_city[c.name]['last']:
            by_city[c.name]['last'] = last_dt

    print(f'[计划] 目标日期: {target_date.date()}')
    print(f'[计划] 落后城市数: {len(by_city)},落后站点数: {len(plan)}')
    print(f'{"城市":<12}{"最新日期":<14}{"站点数":<8}{"补天数":<8}{"将插入":<8}')
    print('-' * 56)
    total_inserts = 0
    for name, info in sorted(by_city.items(), key=lambda x: x[1]['last']):
        ins = info['stations'] * info['days']
        total_inserts += ins
        print(f'{name:<12}{str(info["last"].date()):<14}{info["stations"]:<8}{info["days"]:<8}{ins:<8}')
    print('-' * 56)
    print(f'合计将插入: {total_inserts} 条记录\n')

    if not apply_changes:
        # 干跑:挑一个站点演示生成结果
        if plan:
            st, last_dt, missing = plan[0]
            stats, last = _gather_station_baseline(st.id, target_date)
            if stats and last:
                print(f'[预览] 站点 {st.id} ({st.station_name}),基线(均值±标准差):')
                for f in POLL_FIELDS:
                    m, s = stats[f]
                    print(f'   {f:<6}: mean={m and round(m,2)}, std={s and round(s,2)}')
                print(f'\n[预览] 该站点将生成的 {len(missing)} 条:')
                _simulate_one_station(st, last, stats, missing, dry=True)
        print('\n→ 干跑完成,如确认执行请追加 --apply')
        return

    # 真插入
    inserted = 0
    rng_master = random.Random(42)  # 固定种子,可重现
    for st, last_dt, missing in plan:
        stats, last = _gather_station_baseline(st.id, target_date)
        if not stats or not last:
            continue
        rng = random.Random(rng_master.randint(0, 1 << 30))
        new_records = _simulate_one_station(st, last, stats, missing, dry=False, rng=rng)
        for r in new_records:
            db.session.add(r)
            inserted += 1
    db.session.commit()
    print(f'[完成] 实际插入 {inserted} 条记录')


def _simulate_one_station(station, last_record, stats, missing_dates, dry=False, rng=None):
    """
    用 AR(1)+噪声从 last_record 出发,生成 missing_dates 每天一条记录
    返回 AirQualityRecord 列表(dry=True 时返回空但打印表头几行)
    """
    rng = rng or random.Random()

    prev = {f: _to_float(getattr(last_record, f)) for f in POLL_FIELDS + WEATHER_FIELDS}
    out = []
    for i, dt in enumerate(missing_dates):
        new = {}
        for f in POLL_FIELDS:
            m, s = stats[f]
            v = _next_value(prev.get(f), m, s, lo=0.0, rng=rng)
            new[f] = _round(f, v)
            prev[f] = v
        for f in WEATHER_FIELDS:
            m, s = stats[f]
            lo = 0.0 if f in ('humidity', 'wind_speed', 'rainfall') else -50.0
            v = _next_value(prev.get(f), m, s, lo=lo, rng=rng)
            new[f] = _round(f, v)
            prev[f] = v

        aqi, primary = _calc_cn_aqi(
            pm25=new['pm25'], pm10=new['pm10'], so2=new['so2'],
            no2=new['no2'], co=new['co'], o3=new['o3'],
        )
        level = _aqi_to_level(aqi)

        if dry and i < 3:
            print(f'   {dt.date()} aqi={aqi:>3} pm25={new["pm25"]:>5} pm10={new["pm10"]:>5} '
                  f'level={level} primary={primary}')

        if not dry:
            rec = AirQualityRecord(
                station_id=station.id,
                city_id=station.city_id,
                record_time=dt,
                record_type=last_record.record_type or 'daily',
                aqi=aqi,
                pm25=new['pm25'], pm10=new['pm10'],
                so2=new['so2'], no2=new['no2'],
                co=new['co'], o3=new['o3'],
                temperature=new['temperature'],
                humidity=new['humidity'],
                wind_speed=new['wind_speed'],
                rainfall=new['rainfall'],
                wind_direction=last_record.wind_direction,
                weather_condition=last_record.weather_condition,
                primary_pollutant=primary,
                quality_level=level,
            )
            out.append(rec)
    if dry and len(missing_dates) > 3:
        print(f'   ... (共 {len(missing_dates)} 天,只显示前 3 行)')
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('target_date', help='目标日期,格式 YYYY-MM-DD')
    parser.add_argument('--apply', action='store_true', help='真正写库;不带则只打印计划')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        backfill(args.target_date, apply_changes=args.apply)


if __name__ == '__main__':
    main()
