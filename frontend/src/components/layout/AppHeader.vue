<template>
  <el-header class="app-header">
    <div class="header-brand" @click="$router.push('/')">
      <div class="brand-topline">
      </div>
      <h1 class="brand-title">城市空气质量数据可视化平台</h1>
      <p class="brand-subtitle">可视化 · 预测 · 异常分析</p>
    </div>

    <div class="header-city-shell">
      <div class="header-city">
        <el-select
          v-model="cityStore.currentCityId"
          placeholder="选择演示城市"
          filterable
          @change="onCityChange"
        >
          <el-option
            v-for="city in cityStore.cities"
            :key="city.id"
            :label="city.name"
            :value="city.id"
          />
        </el-select>
      </div>
    </div>

    <div class="header-actions">
      <nav class="header-nav">
        <el-button text class="nav-link" @click="$router.push('/analysis')">数据分析</el-button>
        <el-button text class="nav-link" @click="$router.push('/compare')">城市对比</el-button>
        <el-button text class="nav-link" @click="$router.push('/report')">数据报告</el-button>
        <el-button text class="nav-link" @click="$router.push('/anomaly')">异常管理</el-button>
      </nav>
      <el-button circle class="theme-btn" @click="themeStore.toggle()">
        {{ themeStore.isDark ? '明' : '暗' }}
      </el-button>
    </div>
  </el-header>
</template>

<script setup>
import { computed } from 'vue'
import { useCityStore } from '@/stores/city'
import { useThemeStore } from '@/stores/theme'

const cityStore = useCityStore()
const themeStore = useThemeStore()
const emit = defineEmits(['cityChange'])

const currentDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
})

function onCityChange(val) {
  emit('cityChange', val)
}
</script>

<style scoped>
.app-header {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(220px, 260px) minmax(0, 1.25fr);
  gap: 20px;
  align-items: center;
  min-height: 108px;
  padding: 18px 28px 20px;
  background:
    radial-gradient(circle at top right, rgba(168, 116, 63, 0.16), transparent 24%),
    linear-gradient(135deg, #18282d 0%, #22363d 52%, #142126 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.app-header::after {
  content: '';
  position: absolute;
  left: 28px;
  right: 28px;
  bottom: 0;
  height: 1px;
  background: linear-gradient(90deg, rgba(255,255,255,0), rgba(208,157,105,0.45), rgba(255,255,255,0));
}

.header-brand {
  cursor: pointer;
  display: grid;
  gap: 4px;
}

.brand-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.brand-kicker,
.brand-date,
.city-label {
  font-family: var(--aq-mono);
  font-size: 10px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.brand-kicker {
  color: rgba(244, 234, 220, 0.64);
}

.brand-date {
  color: rgba(244, 234, 220, 0.42);
}

.brand-title {
  font-family: var(--aq-display);
  font-size: 31px;
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: 0.02em;
  color: #f6f0e7;
}

.brand-subtitle {
  font-size: 13px;
  color: rgba(241, 236, 228, 0.72);
}

.header-city-shell {
  display: grid;
  gap: 8px;
}

.city-label {
  color: rgba(244, 234, 220, 0.5);
}

.header-city {
  padding: 10px 12px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
}

.header-city :deep(.el-input__wrapper) {
  background: rgba(255, 250, 243, 0.96) !important;
}

.header-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

.header-nav {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  padding: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
}

.nav-link {
  color: rgba(245, 239, 230, 0.84) !important;
  padding: 10px 14px !important;
  font-weight: 600;
}

.nav-link:hover {
  color: #ffffff !important;
  background: rgba(255, 255, 255, 0.08) !important;
}

.theme-btn {
  color: #f8f2e8 !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  background: rgba(255, 255, 255, 0.06) !important;
}

@media (max-width: 1280px) {
  .app-header {
    grid-template-columns: 1fr;
  }

  .header-actions {
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .header-nav {
    justify-content: flex-start;
    flex-wrap: wrap;
    border-radius: 24px;
  }
}
</style>
