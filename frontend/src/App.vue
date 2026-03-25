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
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  transition: background-color 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              color 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* ====== 亮色主题（默认） ====== */
:root {
  --primary: #0d9488;
  --primary-light: #14b8a6;
  --accent: #e07a5f;
  --accent-light: #f4a261;
  --success: #2d6a4f;
  --warning: #d4a373;
  --danger: #c1121f;
  --bg-page: #eae6e1;
  --bg-card: rgba(255, 255, 255, 0.85);
  --bg-header: linear-gradient(135deg, #1b2a2a 0%, #2c3e3e 50%, #1a2e2e 100%);
  --text-primary: #2c2c2c;
  --text-secondary: #5a5a5a;
  --text-muted: #8a8a8a;
  --border-color: #d5cfc7;
  --shadow: 0 2px 8px rgba(44, 62, 62, 0.08);
  --shadow-hover: 0 6px 20px rgba(44, 62, 62, 0.12);
  --bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  --snap: cubic-bezier(0.68, -0.55, 0.27, 1.55);
  --noise-filter: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E");
}

/* ====== 暗色主题 ====== */
html.dark {
  --bg-page: #141e1e;
  --bg-card: rgba(28, 40, 40, 0.9);
  --text-primary: #e0e6e4;
  --text-secondary: #a0b0ac;
  --text-muted: #6a7a76;
  --border-color: #2a3a38;
  --shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  --shadow-hover: 0 6px 20px rgba(0, 0, 0, 0.35);
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
  background: #1e2e2c !important;
  color: var(--text-secondary) !important;
}
html.dark .el-descriptions__content {
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
}
html.dark .el-table {
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: #1e2e2c;
  --el-table-row-hover-bg-color: #243434;
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
  color: var(--text-primary) !important;
}
html.dark .el-table__row--striped td.el-table__cell {
  background: #1a2828 !important;
}
html.dark .el-select-dropdown {
  background: var(--bg-card) !important;
  border-color: var(--border-color) !important;
}
html.dark .el-select-dropdown__item {
  color: var(--text-primary) !important;
}
html.dark .el-select-dropdown__item.hover {
  background: #243434 !important;
}
html.dark .el-input__wrapper {
  background-color: #1e2e2c !important;
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
  background: #1e2e2c !important;
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
  transform: translateY(-3px) rotate(-0.3deg);
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
