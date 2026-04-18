<template>
  <el-header class="app-header">
    <div class="header-layer"></div>
    <div class="header-left" @click="$router.push('/')">
      <div class="brand-mark">
        <span class="brand-dot"></span>
        <span class="brand-dot brand-dot-alt"></span>
      </div>
      <div class="brand-copy">
        <span class="brand-kicker">Air Research Console</span>
        <h1 class="title">城市空气质量可视化系统</h1>
      </div>
    </div>

    <div class="header-center">
      <div class="city-control">
        <span class="control-label">观测城市</span>
        <el-select
          v-model="cityStore.currentCityId"
          placeholder="请选择城市"
          filterable
          class="city-select"
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

    <div class="header-right">
      <div class="meta-chip date-chip">
        <span class="chip-label">DATE</span>
        <span class="chip-value">{{ currentDate }}</span>
      </div>
      <div class="nav-group">
        <el-button text size="small" class="nav-link" @click="$router.push('/analysis')">数据分析</el-button>
        <el-button text size="small" class="nav-link" @click="$router.push('/compare')">城市对比</el-button>
        <el-button text size="small" class="nav-link" @click="$router.push('/report')">数据报告</el-button>
        <el-button text size="small" class="nav-link" @click="$router.push('/anomaly')">异常管理</el-button>
      </div>
    </div>
  </el-header>
</template>

<script setup>
import { computed } from 'vue'
import { useCityStore } from '@/stores/city'

const cityStore = useCityStore()
const emit = defineEmits(['cityChange'])

const currentDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

function onCityChange(val) {
  emit('cityChange', val)
}
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 30;
  display: grid;
  grid-template-columns: minmax(280px, 1.5fr) minmax(220px, 0.9fr) minmax(320px, 1.4fr);
  align-items: center;
  gap: 18px;
  min-height: 78px;
  padding: 14px 24px;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.18);
  backdrop-filter: blur(18px);
  overflow: hidden;
}

.header-layer {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(39, 211, 195, 0.06), transparent 24%),
    linear-gradient(90deg, transparent, rgba(110, 168, 255, 0.08) 78%, transparent),
    linear-gradient(180deg, rgba(255, 255, 255, 0.02), transparent 70%);
  pointer-events: none;
}

.header-left,
.header-center,
.header-right {
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
  cursor: pointer;
  min-width: 0;
}

.brand-mark {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: 14px;
  border: 1px solid rgba(127, 246, 234, 0.2);
  background: linear-gradient(135deg, rgba(39, 211, 195, 0.14), rgba(110, 168, 255, 0.1));
  box-shadow: inset 0 0 24px rgba(127, 246, 234, 0.08);
}

.brand-dot {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--primary-light);
  top: 8px;
  left: 8px;
  box-shadow: 0 0 18px rgba(127, 246, 234, 0.5);
}

.brand-dot-alt {
  width: 10px;
  height: 10px;
  top: auto;
  left: auto;
  right: 8px;
  bottom: 8px;
  background: var(--accent-light);
  box-shadow: 0 0 18px rgba(110, 168, 255, 0.5);
}

.brand-copy {
  min-width: 0;
}

.brand-kicker {
  display: block;
  margin-bottom: 2px;
  font-size: 11px;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.title {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-center {
  display: flex;
  justify-content: center;
}

.city-control {
  width: min(100%, 280px);
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  background: rgba(8, 20, 34, 0.7);
  box-shadow: inset 0 0 24px rgba(39, 211, 195, 0.04);
}

.control-label {
  display: block;
  margin-bottom: 6px;
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.city-select {
  width: 100%;
  
}

.header-right {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  min-width: 0;
}

.meta-chip {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 9px 12px;
  min-width: 120px;
  border-radius: 14px;
  border: 1px solid var(--border-color);
  background: rgba(8, 20, 34, 0.7);
}

.chip-label {
  font-size: 10px;
  letter-spacing: 0.18em;
  color: var(--text-muted);
}

.chip-value {
  font-size: 13px;
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.nav-group {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  background: rgba(8, 20, 34, 0.72);
  flex-wrap: wrap;
  justify-content: flex-end;
}

.nav-link {
  min-height: 34px;
  padding: 0 12px !important;
  border-radius: 12px !important;
  color: var(--text-secondary) !important;
  font-weight: 600;
}

.nav-link:hover {
  color: var(--text-primary) !important;
  background: rgba(39, 211, 195, 0.12) !important;
}

@media (max-width: 1200px) {
  .app-header {
    grid-template-columns: 1fr;
    gap: 14px;
    height: auto;
    padding: 16px 20px;
  }

  .header-center,
  .header-right {
    justify-content: flex-start;
  }

  .header-right {
    flex-wrap: wrap;
  }

  .nav-group {
    justify-content: flex-start;
  }
}

@media (max-width: 640px) {
  .app-header {
    padding: 14px 14px 16px;
  }

  .header-left {
    align-items: flex-start;
  }

  .title {
    font-size: 18px;
    white-space: normal;
  }

  .city-control,
  .meta-chip,
  .nav-group {
    width: 100%;
  }

  .nav-group {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
