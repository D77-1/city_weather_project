<template>
  <div class="app-shell">
    <div class="shell-aurora shell-aurora-a"></div>
    <div class="shell-aurora shell-aurora-b"></div>
    <div class="shell-grid"></div>
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

// 固定暗色模式，始终添加 dark 类
onMounted(() => {
  document.documentElement.classList.add('dark')
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  min-height: 100%;
  font-family: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
  transition: background-color 0.35s ease, color 0.35s ease;
}

body {
  background:
    radial-gradient(circle at top left, rgba(32, 184, 196, 0.10), transparent 28%),
    radial-gradient(circle at top right, rgba(84, 122, 255, 0.12), transparent 24%),
    linear-gradient(180deg, #08111f 0%, #0b1528 42%, #09111d 100%);
  color: var(--text-primary);
}

.num, [class*="kpi-value"], [class*="kpi-big"], [class*="kpi-num"],
[class*="rt-aqi"], [class*="rt-val"], [class*="ra-val"], [class*="fc-aqi"] {
  font-family: var(--font-mono), sans-serif;
  font-variant-numeric: tabular-nums;
}

:root {
  /* 统一暗色主题 */
  --primary: #27d3c3;
  --primary-light: #7ff6ea;
  --accent: #6ea8ff;
  --accent-light: #a9c8ff;
  --success: #32d296;
  --warning: #f0b65a;
  --danger: #ff6b81;
  --bg-page: #08111f;
  --bg-page-secondary: #0c1728;
  --bg-card: rgba(10, 21, 37, 0.78);
  --bg-card-strong: rgba(12, 26, 44, 0.92);
  --bg-header: linear-gradient(135deg, rgba(8, 18, 33, 0.96) 0%, rgba(10, 23, 41, 0.92) 55%, rgba(7, 15, 29, 0.96) 100%);
  --bg-map: #07111f;
  --text-primary: #edf6ff;
  --text-secondary: #b7c8dc;
  --text-muted: #7c91ab;
  --border-color: rgba(124, 154, 188, 0.18);
  --border-strong: rgba(70, 229, 220, 0.28);
  --shadow: 0 20px 60px rgba(0, 0, 0, 0.26);
  --shadow-hover: 0 24px 80px rgba(0, 0, 0, 0.34);
  --bounce: cubic-bezier(0.22, 1, 0.36, 1);
  --snap: cubic-bezier(0.68, -0.2, 0.27, 1.2);
  --font-mono: 'DIN Alternate', 'Bahnschrift', 'SF Mono', 'Consolas', monospace;
  --noise-filter: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.045'/%3E%3C/svg%3E");

  /* --aq-* 语义变量 (暗色适配) */
  --aq-ink: #edf6ff;
  --aq-ink-soft: #9bb0c8;
  --aq-muted: #6a819a;
  --aq-accent: #f0b65a;
  --aq-primary: #27d3c3;
  --aq-success: #32d296;
  --aq-danger: #ff6b81;
  --aq-mono: 'DIN Alternate', 'Bahnschrift', 'SF Mono', 'Consolas', monospace;
  --aq-display: 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif;
  --aq-shadow-soft: 0 8px 28px rgba(0, 0, 0, 0.22);
  --aq-line-strong: rgba(124, 154, 188, 0.22);

  /* Element Plus 主题色 */
  --el-color-primary: #27d3c3;
  --el-color-primary-light-3: #59ddd0;
  --el-color-primary-light-5: #8de8df;
  --el-color-primary-light-7: #bdf3ee;
  --el-color-primary-light-9: #eafcf9;
  --el-color-primary-dark-2: #14ab9d;
  --el-color-success: #32d296;
  --el-color-warning: #f0b65a;
  --el-color-danger: #ff6b81;
}

.app-shell {
  position: relative;
  min-height: 100vh;
  isolation: isolate;
}

.shell-aurora,
.shell-grid {
  position: fixed;
  inset: 0;
  pointer-events: none;
}

.shell-aurora {
  z-index: -3;
  opacity: 0.9;
}

.shell-aurora-a {
  background:
    radial-gradient(circle at 12% 12%, rgba(39, 211, 195, 0.18), transparent 0 26%),
    radial-gradient(circle at 78% 18%, rgba(110, 168, 255, 0.18), transparent 0 24%);
}

.shell-aurora-b {
  z-index: -2;
  background:
    radial-gradient(circle at 50% 100%, rgba(32, 91, 180, 0.16), transparent 0 28%),
    radial-gradient(circle at 85% 72%, rgba(39, 211, 195, 0.08), transparent 0 18%);
  filter: blur(12px);
}

.shell-grid {
  z-index: -1;
  background-image:
    linear-gradient(rgba(120, 160, 210, 0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(120, 160, 210, 0.06) 1px, transparent 1px),
    var(--noise-filter);
  background-size: 56px 56px, 56px 56px, 256px 256px;
  mask-image: linear-gradient(180deg, rgba(255, 255, 255, 0.65), rgba(255, 255, 255, 0.16));
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  background: radial-gradient(circle at center, transparent 58%, rgba(3, 8, 16, 0.36) 100%);
  pointer-events: none;
  z-index: 0;
}

/* Element Plus 暗色覆盖（始终生效） */
.el-card {
  border-radius: 22px !important;
  border: 1px solid var(--border-color) !important;
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  box-shadow: var(--shadow) !important;
  backdrop-filter: blur(16px);
  transition: transform 0.3s var(--bounce), box-shadow 0.3s var(--bounce), border-color 0.3s ease !important;
}

.el-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-hover) !important;
  border-color: var(--border-strong) !important;
}

.el-card__header {
  padding: 18px 22px !important;
  border-bottom-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

.el-card__body {
  padding: 20px 22px !important;
}

.el-descriptions {
  --el-fill-color-blank: var(--bg-card);
}

.el-descriptions__label {
  background: rgba(12, 28, 46, 0.92) !important;
  color: var(--text-secondary) !important;
}

.el-descriptions__content {
  background: rgba(9, 20, 34, 0.92) !important;
  color: var(--text-primary) !important;
}

.el-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(14, 31, 51, 0.92);
  --el-table-row-hover-bg-color: rgba(39, 211, 195, 0.08);
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-secondary);
  color: var(--text-primary) !important;
}

.el-table__inner-wrapper::before,
.el-table--border::before,
.el-table--border::after,
.el-table td.el-table__cell,
.el-table th.el-table__cell.is-leaf {
  border-color: var(--border-color) !important;
}

.el-table__row--striped td.el-table__cell {
  background: rgba(10, 22, 36, 0.56) !important;
}

.el-select-dropdown,
.el-popper.is-light,
.el-picker__popper.el-popper {
  background: var(--bg-card-strong) !important;
  border-color: var(--border-color) !important;
}

.el-select-dropdown__wrap,
.el-scrollbar__wrap,
.el-select-dropdown__list {
  background: transparent !important;
}

.el-select-dropdown__item,
.el-popper.is-light,
.el-picker-panel,
.el-date-table td .el-date-table-cell__text {
  color: var(--text-primary) !important;
}

.el-select-dropdown__item.hover,
.el-select-dropdown__item:hover,
.el-select-dropdown__item.is-hovering,
.el-select-dropdown__item.selected,
.el-select-dropdown__item.is-selected,
.el-date-table td.available:hover {
  background: rgba(39, 211, 195, 0.15) !important;
  color: var(--text-primary) !important;
}

.el-select-dropdown__item.selected,
.el-select-dropdown__item.is-selected {
  color: var(--primary) !important;
  font-weight: 700;
}

/* select v2 虚拟列表适配 */
.el-select-v2__wrapper,
.el-select__wrapper {
  background-color: rgba(10, 24, 40, 0.88) !important;
  box-shadow: 0 0 0 1px rgba(124, 154, 188, 0.18) inset !important;
}

/* 多选标签 */
.el-select .el-tag {
  background: rgba(39, 211, 195, 0.15) !important;
  border-color: rgba(39, 211, 195, 0.3) !important;
  color: var(--text-primary) !important;
}

.el-input__wrapper,
.el-select .el-input__wrapper,
.el-textarea__inner {
  background-color: rgba(10, 24, 40, 0.88) !important;
  box-shadow: 0 0 0 1px rgba(124, 154, 188, 0.18) inset !important;
  border-radius: 12px !important;
}

.el-input__inner,
.el-textarea__inner {
  color: var(--text-primary) !important;
}

.el-input__wrapper .el-input__inner::placeholder {
  color: var(--text-muted) !important;
}

.el-statistic__head,
.el-page-header__content,
.el-empty__description p,
.el-progress__text {
  color: var(--text-secondary) !important;
}

.el-statistic__number {
  color: var(--text-primary) !important;
}

.el-radio-button__inner {
  background: rgba(11, 24, 40, 0.9) !important;
  color: var(--text-secondary) !important;
  border-color: var(--border-color) !important;
}

.el-radio-button__original-radio:checked + .el-radio-button__inner {
  background: linear-gradient(135deg, rgba(39, 211, 195, 0.95), rgba(110, 168, 255, 0.95)) !important;
  color: #041019 !important;
  box-shadow: 0 10px 24px rgba(39, 211, 195, 0.22) !important;
}

.el-divider {
  border-color: var(--border-color) !important;
}

/* 下拉框弹出层文字颜色 */
.el-select-dropdown__item.is-disabled {
  color: var(--text-muted) !important;
}

.el-popper.is-light .el-popper__arrow::before {
  background: var(--bg-card-strong) !important;
  border-color: var(--border-color) !important;
}

.el-button {
  border-radius: 12px !important;
  transition: transform 0.22s var(--snap), box-shadow 0.22s ease !important;
}

.el-button:active {
  transform: scale(0.97);
}

.el-tag {
  border-radius: 999px !important;
}

</style>
