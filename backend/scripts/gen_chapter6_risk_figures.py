"""
第 6 章 风险评分验证实验三张图生成脚本
---------------------------------------
用法：
    D:/conda_envs/python3.12/python.exe backend/scripts/gen_chapter6_risk_figures.py

输出：
    docs/figures/fig_6_3_confusion_matrix.png
    docs/figures/fig_6_4_weight_sensitivity.png
    docs/figures/fig_6_5_threshold_sensitivity.png

数据来源：
    均为 validate_risk.py 在 143,613 条真实记录上运行的结果，
    与 docs/风险评分算法说明.md §5 及论文 §6.3 完全一致。
"""

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['savefig.dpi'] = 300
mpl.rcParams['figure.dpi'] = 100


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(BASE_DIR, 'docs', 'figures')
os.makedirs(OUT_DIR, exist_ok=True)


def fig_6_3_confusion_matrix():
    """图 6-3：风险评分与 HJ 633 分级混淆矩阵热力图"""
    matrix = np.array([
        [119035, 3453,     0,    0],
        [     0, 15487,    4,    0],
        [     0,  1878, 2911,   39],
        [     0,     0,   17,  789],
    ])
    labels = ['low', 'medium', 'high', 'severe']

    row_sums = matrix.sum(axis=1, keepdims=True)
    percent = matrix / row_sums * 100.0

    fig, ax = plt.subplots(figsize=(7.5, 6))
    im = ax.imshow(percent, cmap='Blues', vmin=0, vmax=100, aspect='auto')

    for i in range(4):
        for j in range(4):
            count = matrix[i, j]
            pct = percent[i, j]
            txt = f'{count:,}\n({pct:.1f}%)'
            color = 'white' if pct > 55 else '#1a1a1a'
            ax.text(j, i, txt, ha='center', va='center',
                    color=color, fontsize=10, fontweight='bold')

    ax.set_xticks(range(4))
    ax.set_yticks(range(4))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel('R 评分预测等级', fontsize=12)
    ax.set_ylabel('HJ 633-2012 实际等级', fontsize=12)
    ax.set_title('图 6-3  风险评分与 HJ 633 分级混淆矩阵\n'
                 '（143,613 条记录，严格一致率 96.55%）', fontsize=12, pad=14)

    cbar = plt.colorbar(im, ax=ax, shrink=0.82)
    cbar.set_label('行百分比 (%)', fontsize=10)

    ax.set_xticks(np.arange(-0.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 4, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1.5)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, 'fig_6_3_confusion_matrix.png')
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()
    print(f'[OK] 图 6-3 已保存：{out_path}')


def fig_6_4_weight_sensitivity():
    """图 6-4：权重敏感性分析分组柱状图"""
    configs = [
        '70/15/5/10\n(默认)',
        '65/20/5/10',
        '75/10/5/10',
        '80/10/5/5',
        '60/20/10/10',
    ]
    strict = [96.55, 31.98, 87.40, 83.89, 36.04]
    tolerance = [100.00, 100.00, 100.00, 100.00, 99.72]

    fig, ax = plt.subplots(figsize=(9, 5.2))
    x = np.arange(len(configs))
    width = 0.36

    bars1 = ax.bar(x - width / 2, strict, width,
                   label='严格一致率', color='#2E5E9B', edgecolor='#1a3d6b', linewidth=0.6)
    bars2 = ax.bar(x + width / 2, tolerance, width,
                   label='±1 级容差一致率', color='#E8A33D', edgecolor='#a6721f', linewidth=0.6)

    for bar in list(bars1) + list(bars2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 1,
                f'{h:.2f}%', ha='center', va='bottom', fontsize=9)

    default_idx = 0
    ax.get_xticklabels()
    for i, bar in enumerate(bars1):
        if i == default_idx:
            bar.set_edgecolor('#c03030')
            bar.set_linewidth(2)

    ax.set_xticks(x)
    ax.set_xticklabels(configs, fontsize=10)
    ax.set_ylabel('一致率 (%)', fontsize=11)
    ax.set_xlabel('权重组合 (R_exposure / R_meteo / R_anomaly / R_trend)', fontsize=11)
    ax.set_title('图 6-4  风险评分权重敏感性分析\n'
                 '（固定阈值 25/38/58，143,613 条记录）', fontsize=12, pad=12)
    ax.set_ylim(0, 115)
    ax.legend(loc='lower center', ncol=2, fontsize=10, frameon=False)
    ax.grid(axis='y', linestyle='--', linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, 'fig_6_4_weight_sensitivity.png')
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()
    print(f'[OK] 图 6-4 已保存：{out_path}')


def fig_6_5_threshold_sensitivity():
    """图 6-5：阈值敏感性分析折线图"""
    thresholds = [
        '15/30/50', '18/33/53', '20/35/55', '22/37/57',
        '25/38/58', '25/40/60', '28/42/62', '30/45/65',
    ]
    strict = [14.80, 44.49, 66.19, 82.36, 96.55, 96.25, 92.21, 89.63]
    tolerance = [99.91, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00, 100.00]

    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    x = np.arange(len(thresholds))

    ax.plot(x, strict, marker='o', linewidth=2.0, markersize=8,
            color='#2E5E9B', label='严格一致率', zorder=3)
    ax.plot(x, tolerance, marker='s', linewidth=2.0, markersize=7,
            color='#E8A33D', label='±1 级容差一致率', zorder=3)

    for xi, yi in zip(x, strict):
        offset = 3.5 if yi < 90 else -5
        va = 'bottom' if offset > 0 else 'top'
        ax.text(xi, yi + offset, f'{yi:.2f}%', ha='center', va=va, fontsize=9, color='#2E5E9B')

    default_idx = thresholds.index('25/38/58')
    ax.annotate('最优阈值\n25 / 38 / 58',
                xy=(default_idx, strict[default_idx]),
                xytext=(default_idx - 1.3, 72),
                fontsize=10, color='#c03030',
                arrowprops=dict(arrowstyle='->', color='#c03030', linewidth=1.2))
    ax.scatter([default_idx], [strict[default_idx]],
               s=220, facecolor='none', edgecolor='#c03030', linewidth=2.2, zorder=4)

    ax.set_xticks(x)
    ax.set_xticklabels(thresholds, fontsize=10)
    ax.set_xlabel('风险等级阈值 (low→med, med→high, high→sev)', fontsize=11)
    ax.set_ylabel('一致率 (%)', fontsize=11)
    ax.set_title('图 6-5  风险评分阈值敏感性分析\n'
                 '（固定权重 70/15/5/10，143,613 条记录）', fontsize=12, pad=12)
    ax.set_ylim(0, 110)
    ax.legend(loc='lower right', fontsize=10, frameon=False)
    ax.grid(axis='both', linestyle='--', linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)

    plt.tight_layout()
    out_path = os.path.join(OUT_DIR, 'fig_6_5_threshold_sensitivity.png')
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()
    print(f'[OK] 图 6-5 已保存：{out_path}')


if __name__ == '__main__':
    print('=' * 60)
    print('第 6 章 风险评分验证实验 - 图表生成')
    print('=' * 60)
    fig_6_3_confusion_matrix()
    fig_6_4_weight_sensitivity()
    fig_6_5_threshold_sensitivity()
    print('=' * 60)
    print(f'全部完成，共 3 张图，已保存到：{OUT_DIR}')
