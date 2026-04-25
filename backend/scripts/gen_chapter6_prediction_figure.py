"""
第 6 章 预测模型对比实验图生成脚本（真实数据）
---------------------------------------------
从数据库调用 run_prediction_pipeline 对 4 个代表城市运行全部 6 种预测
算法，基于返回的 MAE / RMSE / MAPE / R² 指标生成分组柱状图。

用法：
    D:/conda_envs/python3.12/python.exe backend/scripts/gen_chapter6_prediction_figure.py

输出：
    docs/figures/fig_6_6_model_comparison_aqi.png
    docs/figures/fig_6_6_model_comparison_pm25.png
    docs/figures/table_6_4_raw.csv         # 原始数值，可直接填入表 6-4

参数可在 CLI 修改：
    --cities 北京 上海 广州 成都     （默认 4 个）
    --metrics aqi pm25               （默认 2 个）
    --window 7 --days 90
"""

import argparse
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['savefig.dpi'] = 300
mpl.rcParams['figure.dpi'] = 100

from app import create_app
from app.models import City
from app.services.algorithm import run_prediction_pipeline, SUPPORTED_ALGORITHMS


ALGO_LABELS = {
    'moving_average': '移动平均',
    'weighted_moving_average': '加权移动平均',
    'linear_regression': '线性回归',
    'holt_winters': 'Holt-Winters',
    'arima': 'ARIMA',
    'lstm': 'LSTM',
}

METRIC_LABELS = {
    'aqi': 'AQI',
    'pm25': 'PM2.5',
    'pm10': 'PM10',
    'o3': 'O₃',
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE_DIR, 'docs', 'figures')
os.makedirs(OUT_DIR, exist_ok=True)


def collect_evaluation(city_id, metric, window, days):
    """对单个城市 + 单个指标跑 compare 模式，返回 6 种算法的评估字典"""
    result = run_prediction_pipeline(
        city_id, metric=metric, algorithm='moving_average',
        window=window, forecast_days=7, compare=True,
    )
    comparison = result.get('comparison') or []
    table = {}
    for row in comparison:
        algo = row.get('algorithm')
        table[algo] = {
            'mae': row.get('mae'),
            'rmse': row.get('rmse'),
            'mape': row.get('mape'),
            'r2': row.get('r2'),
            'usedFallback': row.get('usedFallback', False),
        }
    return table


def plot_grouped_bar(data_by_city, metric, out_path):
    """
    data_by_city: { '北京': { 'moving_average': {mae, rmse, ...}, ... }, ... }
    画一张 2×2 子图：MAE / RMSE / MAPE / R²，每个子图分组柱状图按城市分组
    """
    algos = list(SUPPORTED_ALGORITHMS)
    cities = list(data_by_city.keys())

    metrics_to_plot = [
        ('mae', 'MAE（平均绝对误差）', False),
        ('rmse', 'RMSE（均方根误差）', False),
        ('mape', 'MAPE（平均绝对百分比误差 %）', False),
        ('r2', 'R²（决定系数）', True),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    axes = axes.flatten()

    color_palette = ['#2E5E9B', '#6aa1d4', '#9ec6e0',
                     '#E8A33D', '#c47a22', '#6B3E8C']

    for ax_idx, (key, title, is_r2) in enumerate(metrics_to_plot):
        ax = axes[ax_idx]
        x = np.arange(len(cities))
        width = 0.85 / len(algos)

        for i, algo in enumerate(algos):
            vals = []
            for city in cities:
                cell = data_by_city[city].get(algo, {})
                v = cell.get(key)
                vals.append(v if v is not None else np.nan)

            offset = (i - (len(algos) - 1) / 2) * width
            bars = ax.bar(x + offset, vals, width,
                          label=ALGO_LABELS[algo],
                          color=color_palette[i], edgecolor='white', linewidth=0.4)

        ax.set_xticks(x)
        ax.set_xticklabels(cities, fontsize=10)
        ax.set_title(title, fontsize=11, pad=8)
        ax.grid(axis='y', linestyle='--', linewidth=0.4, alpha=0.5)
        ax.set_axisbelow(True)
        if is_r2:
            ax.set_ylim(bottom=min(0, ax.get_ylim()[0]))

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=6,
               fontsize=10, frameon=False, bbox_to_anchor=(0.5, -0.02))

    metric_label = METRIC_LABELS.get(metric, metric.upper())
    fig.suptitle(f'图 6-6  预测模型对比实验结果（指标：{metric_label}，近 90 天数据，窗口 = 7）',
                 fontsize=13, y=1.00)
    plt.tight_layout()
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()
    print(f'[OK] 已保存：{out_path}')


def export_csv(data_by_city, metric, out_path):
    """导出原始评估数值为 CSV，方便填入论文表 6-4"""
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['城市', '指标', '算法', 'MAE', 'RMSE', 'MAPE(%)', 'R²', '是否回退'])
        for city in data_by_city:
            for algo in SUPPORTED_ALGORITHMS:
                cell = data_by_city[city].get(algo, {})
                writer.writerow([
                    city,
                    METRIC_LABELS.get(metric, metric.upper()),
                    ALGO_LABELS.get(algo, algo),
                    _fmt(cell.get('mae')),
                    _fmt(cell.get('rmse')),
                    _fmt(cell.get('mape')),
                    _fmt(cell.get('r2')),
                    '是' if cell.get('usedFallback') else '否',
                ])
    print(f'[OK] 已导出：{out_path}')


def _fmt(v):
    if v is None:
        return '-'
    try:
        return f'{float(v):.3f}'
    except (TypeError, ValueError):
        return str(v)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cities', nargs='+', default=['北京', '上海', '广州', '成都'])
    parser.add_argument('--metrics', nargs='+', default=['aqi', 'pm25'])
    parser.add_argument('--window', type=int, default=7)
    parser.add_argument('--days', type=int, default=90)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        city_map = {}
        for name in args.cities:
            c = City.query.filter_by(name=name).first()
            if not c:
                print(f'[WARN] 城市 {name} 在数据库中未找到，已跳过')
                continue
            city_map[name] = c.id

        if not city_map:
            print('[ERROR] 没有可用城市，退出')
            return 1

        for metric in args.metrics:
            print(f'\n===== 指标：{metric.upper()} =====')
            data_by_city = {}
            for city_name, city_id in city_map.items():
                print(f'  > 正在计算 {city_name} / {metric} 的 6 种算法 ...')
                try:
                    table = collect_evaluation(city_id, metric, args.window, args.days)
                except Exception as e:
                    print(f'    [ERROR] {city_name} 失败：{e}')
                    continue
                data_by_city[city_name] = table
                for algo in SUPPORTED_ALGORITHMS:
                    cell = table.get(algo, {})
                    mae = cell.get('mae')
                    mae_str = f'{mae:.3f}' if mae is not None else '-'
                    flag = ' (fallback)' if cell.get('usedFallback') else ''
                    print(f'      · {ALGO_LABELS[algo]}: MAE={mae_str}{flag}')

            if not data_by_city:
                continue

            fig_path = os.path.join(OUT_DIR, f'fig_6_6_model_comparison_{metric}.png')
            plot_grouped_bar(data_by_city, metric, fig_path)

            csv_path = os.path.join(OUT_DIR, f'table_6_4_raw_{metric}.csv')
            export_csv(data_by_city, metric, csv_path)

    print('\n全部完成。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
