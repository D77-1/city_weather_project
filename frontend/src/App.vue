<template>
  <router-view />
</template>

<script setup>
import { provide, toRef } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
provide('isDark', toRef(themeStore, 'isDark'))
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  min-height: 100%;
}

:root {
  --aq-display: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', 'Source Han Serif SC', 'Songti SC', 'STSong', serif;
  --aq-body: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --aq-mono: 'IBM Plex Mono', 'SFMono-Regular', 'Consolas', monospace;

  --aq-primary: #1e5c5a;
  --aq-primary-soft: rgba(30, 92, 90, 0.08);
  --aq-accent: #a8743f;
  --aq-accent-soft: rgba(168, 116, 63, 0.14);
  --aq-danger: #8d3d32;
  --aq-warning: #a07a34;
  --aq-success: #2e6a59;

  --aq-bg: #f4efe7;
  --aq-bg-deep: #ebe3d7;
  --aq-paper: rgba(252, 249, 243, 0.86);
  --aq-paper-strong: rgba(255, 252, 247, 0.96);
  --aq-ink: #1a2529;
  --aq-ink-soft: #4a5a61;
  --aq-muted: #7a878b;
  --aq-line: rgba(26, 37, 41, 0.11);
  --aq-line-strong: rgba(26, 37, 41, 0.2);

  --aq-hero: linear-gradient(135deg, #18292d 0%, #20363b 52%, #152328 100%);
  --aq-shadow: 0 22px 52px rgba(54, 45, 32, 0.08);
  --aq-shadow-soft: 0 12px 28px rgba(54, 45, 32, 0.05);
  --aq-shadow-hover: 0 28px 64px rgba(33, 28, 21, 0.12);

  --aq-radius-xl: 30px;
  --aq-radius-lg: 24px;
  --aq-radius-md: 18px;
  --aq-radius-sm: 12px;

  --primary: var(--aq-primary);
  --accent: var(--aq-accent);
  --success: var(--aq-success);
  --warning: var(--aq-warning);
  --danger: var(--aq-danger);
  --bg-page: var(--aq-bg);
  --bg-card: var(--aq-paper);
  --bg-header: var(--aq-hero);
  --text-primary: var(--aq-ink);
  --text-secondary: var(--aq-ink-soft);
  --text-muted: var(--aq-muted);
  --border-color: var(--aq-line);
  --shadow: var(--aq-shadow);
  --shadow-hover: var(--aq-shadow-hover);

  --el-color-primary: #1e5c5a;
  --el-color-success: #2e6a59;
  --el-color-warning: #a07a34;
  --el-color-danger: #8d3d32;
}

html.dark {
  --aq-primary: #7eb5af;
  --aq-primary-soft: rgba(126, 181, 175, 0.12);
  --aq-accent: #d09d69;
  --aq-accent-soft: rgba(208, 157, 105, 0.16);
  --aq-danger: #d88a79;
  --aq-warning: #cfaf6a;
  --aq-success: #8bc1ae;

  --aq-bg: #11191d;
  --aq-bg-deep: #0c1316;
  --aq-paper: rgba(20, 28, 31, 0.88);
  --aq-paper-strong: rgba(24, 34, 38, 0.96);
  --aq-ink: #edf2ef;
  --aq-ink-soft: #b9c6c1;
  --aq-muted: #7b8c87;
  --aq-line: rgba(237, 242, 239, 0.1);
  --aq-line-strong: rgba(237, 242, 239, 0.18);

  --aq-hero: linear-gradient(135deg, #10171b 0%, #162126 55%, #0d1417 100%);
  --aq-shadow: 0 18px 44px rgba(0, 0, 0, 0.3);
  --aq-shadow-soft: 0 10px 24px rgba(0, 0, 0, 0.22);
  --aq-shadow-hover: 0 24px 58px rgba(0, 0, 0, 0.38);

  --bg-page: var(--aq-bg);
  --bg-card: var(--aq-paper);
  --text-primary: var(--aq-ink);
  --text-secondary: var(--aq-ink-soft);
  --text-muted: var(--aq-muted);
  --border-color: var(--aq-line);
  --shadow: var(--aq-shadow);
  --shadow-hover: var(--aq-shadow-hover);

  --el-color-primary: #7eb5af;
  --el-color-success: #8bc1ae;
  --el-color-warning: #cfaf6a;
  --el-color-danger: #d88a79;
}

body {
  position: relative;
  font-family: var(--aq-body);
  color: var(--aq-ink);
  background:
    radial-gradient(circle at 0% 0%, rgba(168, 116, 63, 0.12), transparent 22%),
    radial-gradient(circle at 100% 18%, rgba(30, 92, 90, 0.12), transparent 26%),
    linear-gradient(180deg, var(--aq-bg) 0%, var(--aq-bg-deep) 100%);
}

body::before,
body::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

body::before {
  background:
    repeating-linear-gradient(
      180deg,
      transparent 0,
      transparent 31px,
      rgba(26, 37, 41, 0.028) 32px
    );
  opacity: 0.55;
}

body::after {
  background:
    radial-gradient(circle at center, transparent 62%, rgba(26, 37, 41, 0.05) 100%);
}

#app {
  position: relative;
  z-index: 1;
}

html,
body,
button,
input,
select,
textarea {
  font-family: var(--aq-body);
}

.page-shell {
  min-height: 100vh;
  color: var(--aq-ink);
  padding-bottom: 28px;
}

.page-section {
  position: relative;
  margin: 0 28px 22px;
}

.section-heading {
  display: grid;
  gap: 7px;
  margin-bottom: 16px;
}

.section-kicker {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-family: var(--aq-mono);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--aq-accent);
}

.section-kicker::after {
  content: '';
  width: 68px;
  height: 1px;
  background: linear-gradient(90deg, var(--aq-accent), transparent);
}

.section-title {
  font-family: var(--aq-display);
  font-size: 34px;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: 0.01em;
  color: var(--aq-ink);
}

.num,
[class*='kpi'],
[class*='aqi'],
[class*='score'],
[class*='stat'],
[class*='rt-aqi'],
[class*='rt-val'],
[class*='ra-val'],
[class*='fc-aqi'] {
  font-family: var(--aq-mono);
  font-variant-numeric: tabular-nums;
}

.el-card {
  position: relative;
  overflow: hidden;
  border-radius: var(--aq-radius-lg) !important;
  border: 1px solid var(--aq-line) !important;
  background: var(--aq-paper) !important;
  box-shadow: var(--aq-shadow) !important;
  backdrop-filter: blur(14px);
}

.el-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--aq-accent-soft), transparent);
  pointer-events: none;
}

.el-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--aq-shadow-hover) !important;
}

.el-card__header {
  padding-top: 18px !important;
  padding-bottom: 14px !important;
  border-bottom: 1px solid var(--aq-line) !important;
  color: var(--aq-ink);
}

.el-card__body {
  position: relative;
}

.el-button,
.el-select .el-input__wrapper,
.el-tag,
.el-radio-button__inner {
  border-radius: 999px !important;
}

.el-button {
  font-weight: 600;
  letter-spacing: 0.02em;
}

.el-button--primary {
  background: linear-gradient(135deg, var(--aq-primary), #28474c) !important;
  border-color: transparent !important;
}

.el-tag {
  border: 1px solid var(--aq-line) !important;
}

.el-select .el-input__wrapper,
.el-input__wrapper {
  background: rgba(255, 255, 255, 0.7) !important;
  box-shadow: 0 0 0 1px var(--aq-line) inset !important;
}

.el-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-border-color: var(--aq-line);
  --el-table-header-bg-color: rgba(26, 37, 41, 0.03);
  --el-table-row-hover-bg-color: rgba(30, 92, 90, 0.06);
  --el-table-text-color: var(--aq-ink);
  --el-table-header-text-color: var(--aq-ink-soft);
}

html.dark .el-select .el-input__wrapper,
html.dark .el-input__wrapper {
  background: rgba(255, 255, 255, 0.04) !important;
}

html.dark .el-table__row--striped td.el-table__cell {
  background: rgba(255, 255, 255, 0.02) !important;
}

html.dark .el-card__header,
html.dark .el-statistic__head,
html.dark .el-empty__description p,
html.dark .el-page-header__content,
html.dark .el-descriptions__label,
html.dark .el-descriptions__content,
html.dark .el-input__inner,
html.dark .el-progress__text {
  color: var(--aq-ink) !important;
}

html.dark .el-radio-button__inner {
  background: rgba(255, 255, 255, 0.03) !important;
  border-color: var(--aq-line) !important;
  color: var(--aq-ink-soft) !important;
}

html.dark .el-radio-button__original-radio:checked + .el-radio-button__inner {
  background: linear-gradient(135deg, var(--aq-primary), #476963) !important;
  color: #091113 !important;
}

@media (max-width: 1200px) {
  .page-section {
    margin: 0 18px 18px;
  }

  .section-title {
    font-size: 28px;
  }
}
</style>
