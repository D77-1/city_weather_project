<template>
  <div class="report-page">
    <AppHeader @city-change="onCityChange" />
    <div class="report-content" v-loading="loading">
      <el-page-header @back="$router.push('/')" style="padding: 16px 24px 0">
        <template #content><span class="page-title">{{ cityName }} 数据报告</span></template>
      </el-page-header>

      <!-- 控制栏 -->
      <div class="ctrl-bar">
        <el-radio-group v-model="period" @change="loadReport">
          <el-radio-button value="30">近30天</el-radio-button>
          <el-radio-button value="90">近90天</el-radio-button>
          <el-radio-button value="180">半年</el-radio-button>
          <el-radio-button value="365">近一年</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 顶部统计 - 不对称两行 -->
      <div class="stat-row" v-if="stats">
        <el-card class="stat-card stat-big" shadow="hover">
          <div class="stat-val" style="color: var(--primary)">{{ stats.avg }}</div>
          <div class="stat-label">平均 AQI</div>
        </el-card>
        <el-card class="stat-card stat-mid" shadow="hover">
          <div class="stat-val" style="color: var(--danger)">{{ stats.max }}</div>
          <div class="stat-label">峰值 AQI</div>
        </el-card>
        <el-card class="stat-card stat-mid" shadow="hover">
          <div class="stat-val" style="color: var(--success)">{{ stats.min }}</div>
          <div class="stat-label">谷值 AQI</div>
        </el-card>
      </div>
      <div class="stat-row stat-row-2" v-if="stats">
        <el-card class="stat-card stat-mid" shadow="hover">
          <div class="stat-val" style="color: var(--success)">{{ stats.good }} 天</div>
          <div class="stat-label">优良天数</div>
        </el-card>
        <el-card class="stat-card stat-big" shadow="hover">
          <div class="stat-val" style="color: var(--primary)">{{ stats.goodRate }}%</div>
          <div class="stat-label">优良率</div>
        </el-card>
        <el-card class="stat-card stat-sm" shadow="hover">
          <div class="stat-val" style="color: var(--warning)">{{ stats.pollutedDays }} 天</div>
          <div class="stat-label">污染天数</div>
        </el-card>
      </div>

      <!-- 图表区: AQI 分布 + 等级占比 - 不对称 -->
      <div class="charts-row">
        <el-card>
          <template #header><span>AQI 分布区间</span></template>
          <EChartWrapper :option="histogramOption" height="300px" />
        </el-card>
        <el-card>
          <template #header><span>空气质量等级占比</span></template>
          <EChartWrapper :option="pieOption" height="300px" />
        </el-card>
      </div>

      <!-- 图表区: 月均趋势 + 污染物月均 -->
      <div class="charts-row">
        <el-card>
          <template #header><span>每月 AQI 均值</span></template>
          <EChartWrapper :option="monthlyOption" height="300px" />
        </el-card>
        <el-card>
          <template #header><span>各污染物月均浓度</span></template>
          <EChartWrapper :option="pollutantMonthlyOption" height="300px" />
        </el-card>
      </div>

      <!-- 天气 vs AQI 相关性 -->
      <el-card style="margin: 0 24px 16px">
        <template #header><span>温度与 AQI 相关性分析</span></template>
        <EChartWrapper :option="scatterOption" height="320px" />
      </el-card>

      <!-- 7日天气预报 -->
      <el-card style="margin: 0 24px 16px" v-if="forecast.length > 0">
        <template #header><span>未来 7 天天气</span></template>
        <div class="forecast-row">
          <div class="fc-card" v-for="f in forecast" :key="f.date">
            <div class="fc-day">{{ f.weekday }}</div>
            <div class="fc-date">{{ f.dateShort }}</div>
            <Icon :icon="weatherIcon(f.weatherText || f.emoji)" width="32" class="fc-icon" />
            <div class="fc-text">{{ f.weatherText }}</div>
            <div class="fc-temp">
              <span class="temp-max">{{ f.tempMax }}°</span>
              <span class="temp-min">{{ f.tempMin }}°</span>
            </div>
            <div class="fc-detail">
              <span><Icon icon="mdi:water-outline" width="12" />{{ f.precipitation }}mm</span>
              <span><Icon icon="mdi:weather-windy" width="12" />{{ f.windSpeedMax }}m/s</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 数据明细表格 -->
      <el-card style="margin: 0 24px 24px">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span>历史数据明细</span>
            <el-button size="small" @click="exportCSV">导出 CSV</el-button>
          </div>
        </template>
        <el-table :data="history.slice(0, 50)" stripe size="small" max-height="400">
          <el-table-column prop="date" label="日期" width="100" />
          <el-table-column prop="aqi" label="AQI" width="70" />
          <el-table-column prop="pm25" label="PM2.5" width="80" />
          <el-table-column prop="pm10" label="PM10" width="80" />
          <el-table-column prop="so2" label="SO₂" width="70" />
          <el-table-column prop="no2" label="NO₂" width="70" />
          <el-table-column prop="co" label="CO" width="70" />
          <el-table-column prop="o3" label="O₃" width="70" />
          <el-table-column prop="temperature" label="温度℃" width="80" />
          <el-table-column prop="humidity" label="湿度%" width="80" />
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCityStore } from '@/stores/city'
import { airQualityApi, weatherApi } from '@/api/modules'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const router = useRouter()
const cityStore = useCityStore()
const loading = ref(false)
const period = ref('90')
const history = ref([])
const forecast = ref([])

const cityName = computed(() => cityStore.currentCity?.name || '全国')

const stats = computed(() => {
  if (history.value.length === 0) return null
  const aqis = history.value.map(r => r.aqi).filter(Boolean)
  const avg = arr => (arr.reduce((s, v) => s + v, 0) / arr.length)
  const good = aqis.filter(v => v <= 100).length
  return {
    avg: avg(aqis).toFixed(0),
    max: Math.max(...aqis),
    min: Math.min(...aqis),
    good,
    goodRate: ((good / aqis.length) * 100).toFixed(1),
    totalDays: aqis.length,
    pollutedDays: aqis.filter(v => v > 100).length,
  }
})

// AQI 分布直方图
const histogramOption = computed(() => {
  const bins = [0, 50, 100, 150, 200, 300, 500]
  const labels = ['优(0-50)', '良(51-100)', '轻度(101-150)', '中度(151-200)', '重度(201-300)', '严重(>300)']
  const colors = ['#2d6a4f', '#d4a373', '#e07a5f', '#c1121f', '#780116', '#4a0010']
  const counts = new Array(6).fill(0)
  history.value.forEach(r => {
    if (!r.aqi) return
    for (let i = 0; i < bins.length - 1; i++) {
      if (r.aqi >= bins[i] && r.aqi <= bins[i + 1]) { counts[i]++; break }
    }
  })
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', name: '天数' },
    series: [{ type: 'bar', data: counts.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })), barWidth: '60%' }],
  }
})

// 等级饼图
const pieOption = computed(() => {
  const levels = ['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染']
  const colors = ['#2d6a4f', '#d4a373', '#e07a5f', '#c1121f', '#780116', '#4a0010']
  const bins = [0, 50, 100, 150, 200, 300, 500]
  const counts = new Array(6).fill(0)
  history.value.forEach(r => {
    if (!r.aqi) return
    for (let i = 0; i < bins.length - 1; i++) {
      if (r.aqi >= bins[i] && r.aqi <= bins[i + 1]) { counts[i]++; break }
    }
  })
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}天 ({d}%)' },
    series: [{
      type: 'pie', radius: ['40%', '70%'],
      data: levels.map((n, i) => ({ name: n, value: counts[i], itemStyle: { color: colors[i] } })).filter(d => d.value > 0),
      label: { formatter: '{b}\n{d}%', fontSize: 11 },
    }],
  }
})

// 月均趋势
const monthlyOption = computed(() => {
  const monthMap = {}
  history.value.forEach(r => {
    const m = r.date?.slice(0, 7)
    if (!m) return
    if (!monthMap[m]) monthMap[m] = []
    monthMap[m].push(r.aqi)
  })
  const months = Object.keys(monthMap).sort()
  const avgs = months.map(m => Math.round(monthMap[m].reduce((s, v) => s + v, 0) / monthMap[m].length))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', name: 'AQI' },
    series: [{
      type: 'bar', data: avgs,
      itemStyle: { color: (p) => p.value > 100 ? '#c1121f' : p.value > 50 ? '#d4a373' : '#2d6a4f' },
      label: { show: true, position: 'top', fontSize: 10 },
    }],
  }
})

// 各污染物月均
const pollutantMonthlyOption = computed(() => {
  const monthMap = {}
  history.value.forEach(r => {
    const m = r.date?.slice(0, 7)
    if (!m) return
    if (!monthMap[m]) monthMap[m] = { pm25: [], pm10: [], no2: [], o3: [] }
    monthMap[m].pm25.push(r.pm25 || 0)
    monthMap[m].pm10.push(r.pm10 || 0)
    monthMap[m].no2.push(r.no2 || 0)
    monthMap[m].o3.push(r.o3 || 0)
  })
  const months = Object.keys(monthMap).sort()
  const avg = arr => arr.length ? Math.round(arr.reduce((s, v) => s + v, 0) / arr.length * 10) / 10 : 0
  const items = [
    { name: 'PM2.5', key: 'pm25', color: '#0d9488' },
    { name: 'PM10', key: 'pm10', color: '#2d6a4f' },
    { name: 'NO₂', key: 'no2', color: '#d4a373' },
    { name: 'O₃', key: 'o3', color: '#e07a5f' },
  ]
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: items.map(i => i.name), bottom: 5 },
    grid: { left: 50, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: months },
    yAxis: { type: 'value', name: 'μg/m³' },
    series: items.map(item => ({
      name: item.name, type: 'line', smooth: true, symbol: 'none',
      data: months.map(m => avg(monthMap[m][item.key])),
      lineStyle: { color: item.color }, itemStyle: { color: item.color },
    })),
  }
})

// 温度 vs AQI 散点
const scatterOption = computed(() => {
  const data = history.value.filter(r => r.temperature != null && r.aqi).map(r => [r.temperature, r.aqi])
  return {
    tooltip: { formatter: p => `温度: ${p.value[0]}℃<br/>AQI: ${p.value[1]}` },
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'value', name: '温度 (℃)' },
    yAxis: { type: 'value', name: 'AQI' },
    series: [{
      type: 'scatter', data,
      symbolSize: 6,
      itemStyle: { color: 'rgba(13,148,136,0.45)' },
    }],
  }
})

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

function exportCSV() {
  const headers = ['日期', 'AQI', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', '温度', '湿度']
  const rows = history.value.map(r => [r.date, r.aqi, r.pm25, r.pm10, r.so2, r.no2, r.co, r.o3, r.temperature, r.humidity])
  const csv = '\uFEFF' + [headers, ...rows].map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${cityName.value}_air_quality_report.csv`
  a.click()
}

async function loadReport() {
  const id = cityStore.currentCityId
  if (!id) return
  loading.value = true
  try {
    const [hist, fc] = await Promise.all([
      airQualityApi.getHistory({ city_id: id, days: Number(period.value) }),
      weatherApi.getForecast(id, 7),
    ])
    history.value = hist
    forecast.value = fc.forecast || []
  } finally {
    loading.value = false
  }
}

function onCityChange(cityId) {
  cityStore.selectCity(cityId)
  loadReport()
}

onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  if (!cityStore.currentCityId && cityStore.cities.length > 0) cityStore.selectCity(cityStore.cities[0].id)
  loadReport()
})
</script>

<style scoped>
.report-page { min-height: 100vh; background: var(--bg-page, #eae6e1); }
.page-title { font-size: 16px; font-weight: 700; }
.ctrl-bar { padding: 12px 24px; }

/* 不对称统计卡片 */
.stat-row { display: flex; gap: 12px; padding: 0 24px 8px; }
.stat-row-2 { padding-top: 0; padding-bottom: 16px; }
.stat-card { text-align: left; }
.stat-big { flex: 1.4; }
.stat-mid { flex: 1; }
.stat-sm { flex: 0.7; }
.stat-val { font-size: 28px; font-weight: 800; letter-spacing: -1px; }
.stat-label { font-size: 12px; color: var(--text-muted, #8a8a8a); margin-top: 4px; }

/* 不对称图表 */
.charts-row { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; padding: 0 24px 16px; }

/* 天气预报卡片 */
.forecast-row { display: flex; gap: 12px; overflow-x: auto; padding: 4px 0; }
.fc-card {
  flex: 0 0 120px; text-align: center;
  background: var(--bg-page, #eae6e1); border-radius: 14px; padding: 14px 8px;
  transition: transform 0.3s var(--bounce, cubic-bezier(0.34, 1.56, 0.64, 1));
}
.fc-card:hover { transform: translateY(-3px) rotate(-1deg); }
.fc-day { font-size: 13px; font-weight: 600; color: var(--text-primary, #2c2c2c); }
.fc-date { font-size: 11px; color: var(--text-muted, #8a8a8a); }
.fc-icon { color: var(--primary, #0d9488); margin: 4px 0; }
.fc-text { font-size: 12px; color: var(--text-secondary, #5a5a5a); }
.fc-temp { margin-top: 6px; }
.temp-max { font-size: 16px; font-weight: 700; color: var(--text-primary, #2c2c2c); }
.temp-min { font-size: 13px; color: var(--text-muted, #8a8a8a); margin-left: 4px; }
.fc-detail { font-size: 10px; color: var(--text-muted, #8a8a8a); margin-top: 6px; display: flex; justify-content: center; gap: 6px; align-items: center; }
</style>
