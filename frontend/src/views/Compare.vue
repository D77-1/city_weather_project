<template>
  <div class="compare-page">
    <AppHeader />
    <div class="compare-content">
      <el-page-header @back="$router.push('/')" style="padding: 16px 24px 0">
        <template #content><span class="page-title">城市空气质量对比</span></template>
      </el-page-header>

      <!-- 城市选择器 -->
      <div class="selector-bar">
        <el-select v-model="selectedIds" multiple filterable placeholder="请选择 2~4 个城市进行对比" style="width: 500px" :max="4">
          <el-option v-for="c in cityStore.cities" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-button type="primary" :loading="loading" :disabled="selectedIds.length < 2" @click="loadCompare">开始对比</el-button>
      </div>

      <template v-if="compareData.length > 0">
        <!-- AQI + 天气概览卡片 - 不对称 -->
        <div class="overview-cards">
          <el-card v-for="(c, i) in compareData" :key="c.cityId" class="city-card" shadow="hover"
            :style="{ flex: i === 0 ? '1.3' : i === compareData.length - 1 ? '0.8' : '1' }">
            <div class="cc-header">
              <span class="cc-name">{{ c.cityName }}</span>
              <el-tag size="small">{{ c.province }}</el-tag>
            </div>
            <div class="cc-aqi" :style="{ color: aqiColor(c.aqi) }">{{ c.aqi }}</div>
            <div class="cc-label">AQI</div>
            <div class="cc-weather" v-if="c.weather">
              <span><Icon :icon="weatherIcon(c.weather.weatherText)" width="16" /> {{ c.weather.weatherText }}</span>
              <span>{{ c.weather.temperature }}℃</span>
              <span><Icon icon="mdi:water-outline" width="14" />{{ c.weather.humidity }}%</span>
            </div>
          </el-card>
        </div>

        <!-- 对比折线图 -->
        <el-card style="margin: 0 24px 16px">
          <template #header><span>30 天 AQI 走势对比</span></template>
          <EChartWrapper :option="trendOption" height="350px" />
        </el-card>

        <!-- 污染物对比 - 不对称 -->
        <div class="charts-row">
          <el-card>
            <template #header><span>污染物浓度雷达</span></template>
            <EChartWrapper :option="radarOption" height="350px" />
          </el-card>
          <el-card>
            <template #header><span>污染物浓度柱状</span></template>
            <EChartWrapper :option="barOption" height="350px" />
          </el-card>
        </div>

        <!-- 详细数据表格 -->
        <el-card style="margin: 0 24px 24px">
          <template #header><span>数据对照表</span></template>
          <el-table :data="tableData" stripe border size="small">
            <el-table-column prop="metric" label="指标" width="100" fixed />
            <el-table-column v-for="c in compareData" :key="c.cityId" :label="c.cityName" align="center">
              <template #default="{ row }">
                <span :style="{ color: row[`color_${c.cityId}`] || '', fontWeight: 600 }">{{ row[`val_${c.cityId}`] }}</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </template>
      <el-empty v-else-if="!loading" description="请先选择城市进行对比" :image-size="120" style="padding: 80px 0" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useCityStore } from '@/stores/city'
import { compareApi } from '@/api/modules'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const cityStore = useCityStore()
const selectedIds = ref([])
const compareData = ref([])
const loading = ref(false)

const COLORS = ['#0d9488', '#e07a5f', '#d4a373', '#c1121f']

async function loadCompare() {
  if (selectedIds.value.length < 2) return
  loading.value = true
  try {
    if (cityStore.cities.length === 0) await cityStore.fetchCities()
    compareData.value = await compareApi.getCities(selectedIds.value)
  } finally {
    loading.value = false
  }
}

const trendOption = computed(() => {
  if (compareData.value.length === 0) return {}
  const allDates = compareData.value[0]?.history?.map(h => h.date) || []
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: compareData.value.map(c => c.cityName), top: 5 },
    grid: { left: 50, right: 20, top: 40, bottom: 50 },
    xAxis: { type: 'category', data: allDates, axisLabel: { rotate: 40, fontSize: 10, formatter: v => v.slice(5) } },
    yAxis: { type: 'value', name: 'AQI' },
    series: compareData.value.map((c, i) => ({
      name: c.cityName,
      type: 'line',
      data: c.history.map(h => h.aqi),
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, color: COLORS[i] },
      itemStyle: { color: COLORS[i] },
    })),
  }
})

const radarOption = computed(() => {
  const indicators = [
    { name: 'PM2.5', max: 200 }, { name: 'PM10', max: 350 },
    { name: 'SO₂', max: 80 }, { name: 'NO₂', max: 120 },
    { name: 'CO', max: 8 }, { name: 'O₃', max: 250 },
  ]
  return {
    legend: { data: compareData.value.map(c => c.cityName), bottom: 5 },
    radar: { indicator: indicators, shape: 'polygon' },
    series: [{
      type: 'radar',
      data: compareData.value.map((c, i) => ({
        name: c.cityName,
        value: [c.pm25, c.pm10, c.so2, c.no2, c.co, c.o3],
        areaStyle: { color: COLORS[i], opacity: 0.15 },
        lineStyle: { color: COLORS[i] },
        itemStyle: { color: COLORS[i] },
      })),
    }],
  }
})

const barOption = computed(() => {
  const metrics = ['PM2.5', 'PM10', 'SO₂', 'NO₂', 'O₃']
  const keys = ['pm25', 'pm10', 'so2', 'no2', 'o3']
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: compareData.value.map(c => c.cityName), bottom: 5 },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: metrics },
    yAxis: { type: 'value', name: 'μg/m³' },
    series: compareData.value.map((c, i) => ({
      name: c.cityName,
      type: 'bar',
      data: keys.map(k => c[k]),
      itemStyle: { color: COLORS[i] },
    })),
  }
})

const tableData = computed(() => {
  const metrics = [
    { key: 'aqi', name: 'AQI', unit: '' },
    { key: 'pm25', name: 'PM2.5', unit: 'μg/m³' },
    { key: 'pm10', name: 'PM10', unit: 'μg/m³' },
    { key: 'so2', name: 'SO₂', unit: 'μg/m³' },
    { key: 'no2', name: 'NO₂', unit: 'μg/m³' },
    { key: 'co', name: 'CO', unit: 'mg/m³' },
    { key: 'o3', name: 'O₃', unit: 'μg/m³' },
  ]
  return metrics.map(m => {
    const row = { metric: `${m.name} ${m.unit}` }
    const vals = compareData.value.map(c => c[m.key] || 0)
    const best = Math.min(...vals)
    const worst = Math.max(...vals)
    compareData.value.forEach(c => {
      const v = c[m.key] || 0
      row[`val_${c.cityId}`] = v
      row[`color_${c.cityId}`] = v === best ? '#2d6a4f' : v === worst ? '#c1121f' : ''
    })
    return row
  })
})

function aqiColor(aqi) {
  if (!aqi) return '#8a8a8a'
  if (aqi <= 50) return '#2d6a4f'
  if (aqi <= 100) return '#d4a373'
  if (aqi <= 150) return '#e07a5f'
  if (aqi <= 200) return '#c1121f'
  return '#780116'
}

function weatherIcon(condition) {
  const map = {
    '晴': 'meteocons:clear-day-fill',
    '多云': 'meteocons:partly-cloudy-day-fill',
    '阴': 'meteocons:overcast-fill',
    '小雨': 'meteocons:drizzle-fill',
    '中雨': 'meteocons:rain-fill',
    '大雨': 'meteocons:rain-fill',
    '暴雨': 'meteocons:thunderstorms-rain-fill',
    '小雪': 'meteocons:snow-fill',
    '中雪': 'meteocons:snow-fill',
    '雨夹雪': 'meteocons:sleet-fill',
  }
  return map[condition] || 'meteocons:partly-cloudy-day-fill'
}

import { onMounted } from 'vue'
onMounted(() => { if (cityStore.cities.length === 0) cityStore.fetchCities() })
</script>

<style scoped>
.compare-page { min-height: 100vh; background: var(--bg-page, #eae6e1); }
.page-title { font-size: 16px; font-weight: 700; }
.selector-bar { display: flex; gap: 12px; padding: 16px 24px; align-items: center; }
.overview-cards { display: flex; gap: 16px; padding: 0 24px 16px; }
.city-card { text-align: left; }
.cc-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.cc-name { font-size: 16px; font-weight: 700; }
.cc-aqi { font-size: 42px; font-weight: 800; line-height: 1.2; letter-spacing: -2px; }
.cc-label { font-size: 12px; color: var(--text-muted, #8a8a8a); }
.cc-weather { display: flex; align-items: center; gap: 12px; margin-top: 10px; font-size: 13px; color: var(--text-secondary, #5a5a5a); }
.charts-row { display: grid; grid-template-columns: 1.3fr 0.9fr; gap: 16px; padding: 0 24px 16px; }
</style>
