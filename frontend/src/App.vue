<template>
  <router-view />
</template>

<script setup>
import { provide } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { toRef } from 'vue'

const themeStore = useThemeStore()
provide('isDark', toRef(themeStore, 'isDark'))
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: -apple-system, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* 数字专用等宽字体 */
.num, [class*="kpi-value"], [class*="kpi-big"], [class*="kpi-num"],
[class*="rt-aqi"], [class*="rt-val"], [class*="ra-val"], [class*="fc-aqi"] {
  font-family: var(--font-mono), sans-serif;
  font-variant-numeric: tabular-nums;
}

/* ====== 亮色主题 — 冷色环境监测风 ====== */
:root {
  --primary: #0d9488;
  --primary-light: #14b8a6;
  --accent: #e07a5f;
  --accent-light: #f4a261;
  --success: #059669;
  --warning: #d97706;
  --danger: #dc2626;
  --bg-page: #f0f4f8;
  --bg-card: rgba(255, 255, 255, 0.92);
  --bg-header: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  --bg-map: #0f1a2e;
  --text-primary: #1e293b;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --shadow: 0 1px 3px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-hover: 0 4px 12px rgba(15, 23, 42, 0.10);
  --bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --snap: cubic-bezier(0.68, -0.55, 0.27, 1.55);
  --font-mono: 'DIN Alternate', 'Menlo', 'SF Mono', 'Consolas', monospace;
  --noise-filter: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
}

/* ====== 暗色主题 ====== */
html.dark {
  --bg-page: #0f172a;
  --bg-card: rgba(30, 41, 59, 0.92);
  --bg-map: #0a1020;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --border-color: #334155;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.4);
}

/* 噪点纹理背景 */
body::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: var(--noise-filter);
  background-repeat: repeat;
  background-size: 256px 256px;
  pointer-events: none;
  z-index: 0;
  opacity: 0.5;
}

/* Element Plus 暗色覆盖 - 定制化 */
html.dark .el-card {
  background-color: var(--bg-card) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
  backdrop-filter: blur(8px);
}
html.dark .el-card__header {
  border-bottom-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}
html.dark .el-descriptions {
  --el-fill-color-blank: var(--bg-card);
}
html.dark .el-descriptions__label {
  background: #1e293b !important;
  color: var(--text-secondary) !important;
}
html.dark .el-descriptions__content {
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
}
html.dark .el-table {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: #1e293b;
  --el-table-row-hover-bg-color: #1e3a5f;
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
  color: var(--text-primary) !important;
}
html.dark .el-table__row--striped td.el-table__cell {
  background: #162032 !important;
}
html.dark .el-select-dropdown {
  background: var(--bg-card) !important;
  border-color: var(--border-color) !important;
}
html.dark .el-select-dropdown__item {
  color: var(--text-primary) !important;
}
html.dark .el-select-dropdown__item.hover {
  background: #1e3a5f !important;
}
html.dark .el-input__wrapper {
  background-color: #1e293b !important;
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}
html.dark .el-input__inner {
  color: var(--text-primary) !important;
}
html.dark .el-statistic__head {
  color: var(--text-secondary) !important;
}
html.dark .el-statistic__number {
  color: var(--text-primary) !important;
}
html.dark .el-page-header__content {
  color: var(--text-primary) !important;
}
html.dark .el-radio-button__inner {
  background: #1e293b !important;
  color: var(--text-secondary) !important;
  border-color: var(--border-color) !important;
}
html.dark .el-radio-button__original-radio:checked + .el-radio-button__inner {
  background: var(--primary) !important;
  color: #fff !important;
}
html.dark .el-empty__description p {
  color: var(--text-muted) !important;
}
html.dark .el-progress__text {
  color: var(--text-primary) !important;
}
html.dark .el-divider {
  border-color: var(--border-color) !important;
}

/* Element Plus 全局定制 - 圆角加大, 去掉默认感 */
.el-card {
  border-radius: 14px !important;
  border: 1px solid var(--border-color) !important;
  backdrop-filter: blur(8px);
  transition: transform 0.3s var(--bounce), box-shadow 0.3s var(--bounce) !important;
}
.el-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-hover) !important;
}
.el-button {
  border-radius: 10px !important;
  transition: transform 0.2s var(--snap) !important;
}
.el-button:active {
  transform: scale(0.96);
}
.el-tag {
  border-radius: 8px !important;
}
.el-select .el-input__wrapper {
  border-radius: 10px !important;
}

/* Element Plus 主色覆盖 */
:root {
  --el-color-primary: #0d9488;
  --el-color-primary-light-3: #3ab0a5;
  --el-color-primary-light-5: #86d3cc;
  --el-color-primary-light-7: #b3e4e0;
  --el-color-primary-light-9: #e6f5f3;
  --el-color-primary-dark-2: #0a756b;
  --el-color-success: #2d6a4f;
  --el-color-warning: #d4a373;
  --el-color-danger: #c1121f;
}
</style>
