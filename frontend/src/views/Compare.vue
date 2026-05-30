<template>
  <div class="compare-page page-shell">
    <AppHeader />

    <section class="page-section compare-intro">
      <div class="section-heading">
        <span class="section-kicker">COMPARISON</span>
        <h2 class="section-title">城市空气质量对比</h2>
      </div>

      <el-card class="compare-intro-card">
        <div class="compare-toolbar">
          <div>
            <p class="toolbar-kicker">对比说明</p>
            <h3 class="toolbar-title">选择 2~4 个城市，展示空气质量、天气与污染物差异</h3>
          </div>
          <div class="selector-bar">
            <el-select v-model="selectedIds" multiple filterable placeholder="请选择 2~4 个城市进行对比" style="width: 420px" :max="4">
              <el-option v-for="c in cityStore.cities" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
            <el-button type="primary" :loading="loading" :disabled="selectedIds.length < 2" @click="loadCompare">开始对比</el-button>
          </div>
        </div>
      </el-card>
    </section>

    <template v-if="compareData.length > 0">
      <section class="page-section compare-overview">
        <div class="section-heading compact-heading">
          <span class="section-kicker">OVERVIEW</span>
          <h2 class="section-title">对比总览</h2>
        </div>
        <div class="overview-cards">
          <el-card v-for="(c, i) in compareData" :key="c.cityId" class="city-card" :style="{ flex: i === 0 ? '1.28' : i === compareData.length - 1 ? '0.92' : '1' }">
            <div class="cc-header">
              <div>
                <span class="cc-name">{{ c.cityName }}</span>
                <p class="cc-province">{{ c.province }}</p>
              </div>
              <el-tag size="small" effect="plain">样本城市</el-tag>
            </div>
            <div class="cc-aqi" :style="{ color: aqiColor(c.aqi) }">{{ c.aqi }}</div>
            <div class="cc-label">空气质量指数 AQI</div>
            <div class="cc-weather" v-if="c.weather">
              <span><img :src="weatherIcon(c.weather.weatherText)" width="18" height="18" alt="" class="cc-weather-svg" /> {{ c.weather.weatherText }}</span>
              <span>{{ c.weather.temperature }}℃</span>
              <span><Icon icon="mdi:water-outline" width="14" /> {{ c.weather.humidity }}%</span>
            </div>
          </el-card>
        </div>
      </section>

      <section class="page-section compare-trend">
        <div class="section-heading compact-heading">
          <span class="section-kicker">TREND</span>
          <h2 class="section-title">30 天趋势对照</h2>
        </div>
        <el-card class="report-card">
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>30 天 AQI 走势对比</span>
                <p>比较多城市空气质量变化节奏与波动幅度。</p>
              </div>
            </div>
          </template>
          <EChartWrapper :option="trendOption" height="350px" />
        </el-card>
      </section>

      <section class="page-section compare-analysis-grid">
        <div>
          <div class="section-heading compact-heading">
            <span class="section-kicker">POLLUTANTS</span>
            <h2 class="section-title">污染物结构对比</h2>
          </div>
          <div class="charts-row">
            <el-card class="report-card">
              <template #header>
                <div class="card-header card-header--stacked">
                  <div>
                    <span>污染物浓度雷达</span>
                    <p>适合快速展示多指标结构差异。</p>
                  </div>
                </div>
              </template>
              <EChartWrapper :option="radarOption" height="350px" />
            </el-card>
            <el-card class="report-card">
              <template #header>
                <div class="card-header card-header--stacked">
                  <div>
                    <span>污染物浓度柱状</span>
                    <p>直观比较主要污染物绝对值高低。</p>
                  </div>
                </div>
              </template>
              <EChartWrapper :option="barOption" height="350px" />
            </el-card>
          </div>
        </div>

        <div>
          <div class="section-heading compact-heading">
            <span class="section-kicker">DETAILS</span>
            <h2 class="section-title">数据对照表</h2>
          </div>
          <el-card class="report-card table-card">
            <template #header>
              <div class="card-header card-header--stacked">
                <div>
                  <span>指标对照</span>
                  <p>绿色表示较优值，红色表示较差值。</p>
                </div>
              </div>
            </template>
            <el-table :data="tableData" stripe border size="small">
              <el-table-column prop="metric" label="指标" width="100" fixed />
              <el-table-column v-for="c in compareData" :key="c.cityId" :label="c.cityName" align="center">
                <template #default="{ row }">
                  <span :style="{ color: row[`color_${c.cityId}`] || '', fontWeight: 600 }">{{ row[`val_${c.cityId}`] }}</span>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>
      </section>
    </template>

    <section v-else-if="!loading" class="page-section">
      <el-card class="empty-card">
        <el-empty description="请先选择城市进行对比" :image-size="120" />
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCityStore } from '@/stores/city'
import { compareApi } from '@/api/modules'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const cityStore = useCityStore()
const selectedIds = ref([])
const compareData = ref([])
const loading = ref(false)

const COLORS = ['#1e5c5a', '#a8743f', '#8d3d32', '#5f6f52']

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
    legend: { data: compareData.value.map(c => c.cityName), top: 8, textStyle: { color: '#b7c8dc' } },
    grid: { left: 50, right: 20, top: 56, bottom: 50 },
    xAxis: {
      type: 'category',
      data: allDates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(124,154,188,0.18)' } },
      axisLabel: { rotate: 40, fontSize: 10, formatter: v => v.slice(5), color: '#9bb0c8' },
    },
    yAxis: {
      type: 'value',
      name: 'AQI',
      nameTextStyle: { color: '#9bb0c8' },
      splitLine: { lineStyle: { color: 'rgba(124,154,188,0.12)' } },
    },
    series: compareData.value.map((c, i) => ({
      name: c.cityName,
      type: 'line',
      data: c.history.map(h => h.aqi),
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2.5, color: COLORS[i] },
      itemStyle: { color: COLORS[i] },
      areaStyle: i === 0 ? { color: 'rgba(30,92,90,0.08)' } : undefined,
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
    legend: { data: compareData.value.map(c => c.cityName), bottom: 4, textStyle: { color: '#b7c8dc' } },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitArea: { areaStyle: { color: ['rgba(39,211,195,0.03)', 'rgba(110,168,255,0.03)'] } },
      axisName: { color: '#9bb0c8' },
    },
    series: [{
      type: 'radar',
      data: compareData.value.map((c, i) => ({
        name: c.cityName,
        value: [c.pm25, c.pm10, c.so2, c.no2, c.co, c.o3],
        areaStyle: { color: COLORS[i], opacity: 0.12 },
        lineStyle: { color: COLORS[i], width: 2 },
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
    legend: { data: compareData.value.map(c => c.cityName), bottom: 4, textStyle: { color: '#b7c8dc' } },
    grid: { left: 50, right: 20, top: 24, bottom: 54 },
    xAxis: { type: 'category', data: metrics, axisLabel: { color: '#9bb0c8' } },
    yAxis: { type: 'value', name: 'μg/m³', nameTextStyle: { color: '#9bb0c8' }, splitLine: { lineStyle: { color: 'rgba(124,154,188,0.12)' } } },
    series: compareData.value.map((c, i) => ({
      name: c.cityName,
      type: 'bar',
      barMaxWidth: 18,
      data: keys.map(k => c[k]),
      itemStyle: { color: COLORS[i], borderRadius: [8, 8, 0, 0] },
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
      row[`color_${c.cityId}`] = v === best ? '#32d296' : v === worst ? '#ff6b81' : ''
    })
    return row
  })
})

function aqiColor(aqi) {
  if (!aqi) return '#8a8a8a'
  if (aqi <= 50) return '#2d6a4f'
  if (aqi <= 100) return '#a8743f'
  if (aqi <= 150) return '#c86b4b'
  if (aqi <= 200) return '#b42318'
  return '#780116'
}

import clearSvg from '@/assets/weather/clear.svg'
import partlyCloudySvg from '@/assets/weather/partly-cloudy.svg'
import overcastSvg from '@/assets/weather/overcast.svg'
import fogSvg from '@/assets/weather/fog.svg'
import hazeSvg from '@/assets/weather/haze.svg'
import dustSvg from '@/assets/weather/dust.svg'
import drizzleSvg from '@/assets/weather/drizzle.svg'
import rainSvg from '@/assets/weather/rain.svg'
import heavyRainSvg from '@/assets/weather/heavy-rain.svg'
import thunderstormSvg from '@/assets/weather/thunderstorm.svg'
import snowSvg from '@/assets/weather/snow.svg'
import heavySnowSvg from '@/assets/weather/heavy-snow.svg'
import sleetSvg from '@/assets/weather/sleet.svg'

function weatherIcon(condition) {
  if (!condition) return overcastSvg
  const key = String(condition).trim()
  const map = {
    '晴': clearSvg,
    '晴间多云': partlyCloudySvg,
    '多云': partlyCloudySvg,
    '阴': overcastSvg,
    '雾': fogSvg,
    '薄雾': fogSvg,
    '霾': hazeSvg,
    '浮尘': dustSvg,
    '扬沙': dustSvg,
    '沙尘暴': dustSvg,
    '阵雨': rainSvg,
    '雷阵雨': thunderstormSvg,
    '毛毛雨': drizzleSvg,
    '小雨': drizzleSvg,
    '中雨': rainSvg,
    '大雨': heavyRainSvg,
    '暴雨': thunderstormSvg,
    '大暴雨': thunderstormSvg,
    '特大暴雨': thunderstormSvg,
    '冻雨': sleetSvg,
    '小雪': snowSvg,
    '中雪': snowSvg,
    '大雪': heavySnowSvg,
    '暴雪': heavySnowSvg,
    '阵雪': snowSvg,
    '雨夹雪': sleetSvg,
  }
  if (map[key]) return map[key]
  if (key.includes('雷')) return thunderstormSvg
  if (key.includes('暴雨')) return thunderstormSvg
  if (key.includes('大雨')) return heavyRainSvg
  if (key.includes('雨夹雪')) return sleetSvg
  if (key.includes('大雪') || key.includes('暴雪')) return heavySnowSvg
  if (key.includes('雪')) return snowSvg
  if (key.includes('雨')) return rainSvg
  if (key.includes('雾')) return fogSvg
  if (key.includes('霾')) return hazeSvg
  if (key.includes('尘') || key.includes('沙')) return dustSvg
  if (key.includes('多云') || key.includes('晴')) return partlyCloudySvg
  if (key.includes('阴')) return overcastSvg
  return overcastSvg
}

onMounted(() => { if (cityStore.cities.length === 0) cityStore.fetchCities() })
</script>

<style scoped>
.compare-page {
  padding-bottom: 28px;
}

/* 卡片使用全局暗色主题，不再单独覆盖 */

.compare-toolbar,
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.toolbar-kicker {
  font-family: var(--aq-mono);
  font-size: 20px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--aq-accent);
}

.toolbar-title {
  margin-top: 10px;
  font-family: var(--aq-display);
  font-size: 32px;
  line-height: 1.14;
  color: var(--aq-ink);
}

.selector-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.overview-cards {
  display: flex;
  gap: 16px;
}

.city-card {
  padding: 24px;
}

.cc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.cc-name {
  display: block;
  font-family: var(--aq-display);
  font-size: 28px;
  color: var(--aq-ink);
}

.cc-province,
.cc-label,
.cc-weather,
.card-header p {
  color: var(--aq-ink-soft);
}

.cc-province {
  margin-top: 4px;
}

.cc-aqi {
  margin-top: 18px;
  font-size: 64px;
  line-height: 0.95;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.cc-label {
  margin-top: 6px;
  font-family: var(--aq-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.cc-weather {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 14px;
  flex-wrap: wrap;
  font-size: 13px;
}

.card-header--stacked p,
.card-header p {
  margin-top: 4px;
}

.compare-analysis-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(360px, 0.95fr);
  gap: 18px;
}

.charts-row {
  display: grid;
  gap: 16px;
}

.table-card :deep(.el-table) {
  --el-table-header-bg-color: rgba(39, 211, 195, 0.06);
}

.empty-card {
  padding: 24px;
}

@media (max-width: 1200px) {
  .compare-toolbar,
  .compare-analysis-grid,
  .overview-cards {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
