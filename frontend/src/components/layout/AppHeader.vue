<template>
  <el-header class="app-header">
    <div class="header-left" @click="$router.push('/')" style="cursor: pointer">
      <h1 class="title">城市空气质量可视化系统</h1>
    </div>
    <div class="header-center">
      <el-select
        v-model="cityStore.currentCityId"
        placeholder="请选择城市"
        filterable
        style="width: 200px"
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
    <div class="header-right">
      <span class="date-text">{{ currentDate }}</span>
      <el-button
        :icon="themeStore.isDark ? 'Sunny' : 'Moon'"
        circle
        size="small"
        class="theme-btn"
        @click="themeStore.toggle()"
      />
      <el-button text size="small" class="nav-link" @click="$router.push('/compare')">城市对比</el-button>
      <el-button text size="small" class="nav-link" @click="$router.push('/report')">数据报告</el-button>
      <el-button text size="small" class="nav-link" @click="$router.push('/anomaly')">异常检测</el-button>
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
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

function onCityChange(val) {
  emit('cityChange', val)
}
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #1b2a2a 0%, #2c3e3e 50%, #1a2e2e 100%);
  color: #e0e6e4;
  padding: 0 24px;
  height: 60px;
  border-bottom: 1px solid #3a4e4c;
}
.header-left {
  flex: 1.5;
}
.title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 1px;
  background: linear-gradient(90deg, #14b8a6, #e07a5f);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header-center {
  flex: 0.8;
  display: flex;
  justify-content: center;
}
.header-right {
  flex: 1.2;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}
.date-text {
  font-size: 13px;
  color: #6a7a76;
}
.theme-btn {
  color: #e0e6e4 !important;
  border-color: #3a4e4c !important;
  background: transparent !important;
}
.theme-btn:hover {
  background: rgba(255,255,255,0.08) !important;
  transform: rotate(20deg);
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.nav-link {
  color: #a0b0ac !important;
  font-weight: 600;
}
.nav-link:hover {
  color: #14b8a6 !important;
}
</style>
