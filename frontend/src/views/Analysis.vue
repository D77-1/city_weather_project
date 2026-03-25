<template>
  <div class="analysis-page">
    <AppHeader @city-change="onCityChange" />

    <div class="analysis-content">
      <!-- 顶部城市选择 + 时间范围 -->
      <div class="analysis-toolbar">
        <div class="toolbar-left">
          <Icon icon="mdi:chart-areaspline" width="22" style="color: var(--primary)" />
          <span class="toolbar-title">数据分析</span>
          <el-tag effect="plain" size="small">{{ selectedCityName }}</el-tag>
        </div>
        <el-radio-group v-model="days" size="small" @change="onDaysChange">
          <el-radio-button :value="30">近30天</el-radio-button>
          <el-radio-button :value="60">近60天</el-radio-button>
          <el-radio-button :value="90">近90天</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 第一行: 趋势图(宽) + 雷达图(窄) -->
      <div class="row-asymmetric">
        <el-card class="flex-grow">
          <template #header>
            <div class="card-header">
              <span>AQI 走势与预测</span>
              <el-tag size="small" effect="plain" type="warning">含移动平均 + 置信区间</el-tag>
            </div>
          </template>
          <TrendLine
            :trend-data="aqStore.trendWithPrediction"
            :title="`${selectedCityName} AQI 走势`"
            height="340px"
          />
        </el-card>
        <el-card class="flex-side">
          <RadarChart :pollutant-data="currentPollutants" :city-name="selectedCityName" height="340px" />
        </el-card>
      </div>

      <!-- 第二行: 污染物浓度折线(宽) + 天气历史(窄) -->
      <div class="row-asymmetric">
        <el-card class="flex-grow">
          <template #header>
            <div class="card-header">
              <span>六项污染物浓度趋势</span>
              <el-tag size="small" effect="plain" type="success">Open-Meteo 真实数据</el-tag>
            </div>
          </template>
          <EChartWrapper :option="pollutantLineOption" height="300px" />
        </el-card>
        <el-card class="flex-side">
          <template #header>
            <div class="card-header">
              <span>气温与降水 (近{{ days }}天)</span>
              <el-tag size="small" effect="plain" type="success">真实数据</el-tag>
            </div>
          </template>
          <EChartWrapper :option="weatherChartOption" height="300px" />
        </el-card>
      </div>

      <!-- 第三行: 异常检测 + 统计摘要 -->
      <div class="row-asymmetric">
        <el-card class="flex-grow" v-if="aqStore.anomalyResult">
          <template #header><span>IQR 异常检测</span></template>
          <el-row :gutter="16">
            <el-col :span="6"><el-statistic title="数据点" :value="aqStore.anomalyResult.total_points" /></el-col>
            <el-col :span="6">
              <el-statistic title="异常数" :value="aqStore.anomalyResult.anomaly_count">
                <template #suffix><el-tag type="danger" size="small" v-if="aqStore.anomalyResult.anomaly_count > 0">需关注</el-tag></template>
              </el-statistic>
            </el-col>
            <el-col :span="6"><el-statistic title="Q1 ~ Q3" :value="`${aqStore.anomalyResult.q1} ~ ${aqStore.anomalyResult.q3}`" /></el-col>
            <el-col :span="6"><el-statistic title="正常范围" :value="`${aqStore.anomalyResult.lower_bound} ~ ${aqStore.anomalyResult.upper_bound}`" /></el-col>
          </el-row>
          <el-table
            v-if="aqStore.anomalyResult.anomalies?.length > 0"
            :data="aqStore.anomalyResult.anomalies.slice(0, 10)"
            stripe size="small" style="margin-top: 16px" max-height="200"
          >
            <el-table-column prop="date" label="日期" width="110" />
            <el-table-column prop="value" label="AQI" width="80">
              <template #default="{ row }"><span style="color: var(--danger); font-weight: 700">{{ row.value }}</span></template>
            </el-table-column>
            <el-table-column prop="type" label="方向" width="80">
              <template #default="{ row }"><el-tag :type="row.type === 'high' ? 'danger' : 'primary'" size="small">{{ row.type === 'high' ? '偏高' : '偏低' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="severity" label="程度">
              <template #default="{ row }"><el-tag :type="row.severity === 'severe' ? 'danger' : row.severity === 'moderate' ? 'warning' : 'info'" size="small">{{ { severe: '严重', moderate: '中度', mild: '轻度' }[row.severity] }}</el-tag></template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="flex-side" v-if="historyStats">
          <template #header><span>近{{ days }}天统计</span></template>
          <div class="stat-grid">
            <div class="stat-item" v-for="s in historyStats" :key="s.label">
              <div class="stat-val" :style="{ color: s.color || 'var(--text-primary)' }">{{ s.value }}<small v-if="s.suffix">{{ s.suffix }}</small></div>
              <div class="stat-label">{{ s.label }}</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useCityStore } from '@/stores/city'
import { useAirQualityStore } from '@/stores/airQuality'
import { realAqiApi, weatherApi } from '@/api/modules'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import TrendLine from '@/components/charts/TrendLine.vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const cityStore = useCityStore()
const aqStore = useAirQualityStore()

const days = ref(60)
const realHistory = ref([])       // Open-Meteo 真实历史 AQI
const weatherHistory = ref([])    // Open-Meteo 真实历史天气

const selectedCityName = computed(() => cityStore.currentCity?.name || '全国')

const currentPollutants = computed(() => {
  const d = aqStore.latestData.find((d) => d.cityId === cityStore.currentCityId)
  if (!d) return {}
  return { pm25: d.pm25, pm10: d.pm10, so2: d.so2, no2: d.no2, co: d.co, o3: d.o3 }
})

// 六项污染物折线图 — 使用真实数据
const pollutantLineOption = computed(() => {
  const h = realHistory.value
  if (!h.length) return {}
  const dates = h.map(r => r.date)
  const make = (key, name, color) => ({
    name, type: 'line', data: h.map(r => r[key]), smooth: true,
    symbol: 'none', lineStyle: { width: 1.5, color }, itemStyle: { color },
  })
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { fontSize: 11 } },
    grid: { left: 50, right: 16, top: 36, bottom: 45 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 35, fontSize: 10, formatter: v => v.slice(5) } },
    yAxis: { type: 'value' },
    series: [
      make('pm25', 'PM2.5', '#0d9488'),
      make('pm10', 'PM10', '#0891b2'),
      make('so2', 'SO₂', '#7c3aed'),
      make('no2', 'NO₂', '#e07a5f'),
      make('co', 'CO', '#d97706'),
      make('o3', 'O₃', '#059669'),
    ],
  }
})

// 气温+降水双轴图 — 使用真实天气历史
const weatherChartOption = computed(() => {
  const h = weatherHistory.value
  if (!h.length) return {}
  const dates = h.map(r => r.date)
  const temps = h.map(r => r.tempMean || r.tempMax)
  const rain = h.map(r => r.precipitation || 0)
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { fontSize: 11 } },
    grid: { left: 45, right: 45, top: 36, bottom: 45 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 35, fontSize: 10, formatter: v => v.slice(5) } },
    yAxis: [
      { type: 'value', name: '℃', position: 'left' },
      { type: 'value', name: 'mm', position: 'right', splitLine: { show: false } },
    ],
    series: [
      { name: '温度', type: 'line', data: temps, smooth: true, symbol: 'none', lineStyle: { color: '#dc2626' }, itemStyle: { color: '#dc2626' } },
      { name: '降水', type: 'bar', data: rain, yAxisIndex: 1, barWidth: '40%', itemStyle: { color: 'rgba(13,148,136,0.4)' } },
    ],
  }
})

// 统计摘要 — 使用真实数据
const historyStats = computed(() => {
  const h = realHistory.value
  if (!h || !h.length) return null
  const aqiArr = h.map(r => r.aqi).filter(Boolean)
  const pm25Arr = h.map(r => r.pm25).filter(Boolean)
  const avg = arr => (arr.reduce((s, v) => s + v, 0) / arr.length).toFixed(1)
  const goodDays = aqiArr.filter(v => v <= 100).length
  return [
    { label: 'AQI 均值', value: avg(aqiArr), color: 'var(--primary)' },
    { label: 'AQI 峰值', value: Math.max(...aqiArr), color: 'var(--danger)' },
    { label: 'AQI 最低', value: Math.min(...aqiArr), color: 'var(--success)' },
    { label: 'PM2.5 均值', value: avg(pm25Arr), suffix: ' μg/m³' },
    { label: '优良天数', value: goodDays, suffix: ' 天', color: 'var(--success)' },
    { label: '优良率', value: ((goodDays / aqiArr.length) * 100).toFixed(1), suffix: '%', color: 'var(--success)' },
  ]
})

async function loadData() {
  const cityId = cityStore.currentCityId
  if (!cityId) return
  // 同时拉取 mock 数据（预测/异常检测依赖）和真实数据（图表展示）
  await Promise.all([
    aqStore.fetchLatest(),
    aqStore.fetchPrediction(cityId),
    aqStore.fetchAnomalyDetect(cityId),
  ])
  // 真实 AQI 历史（Open-Meteo CAMS，数据到今天）
  realAqiApi.getHistory(cityId, days.value).then(d => {
    realHistory.value = d.history || []
  }).catch(() => { realHistory.value = [] })
  // 真实天气历史
  weatherApi.getHistory(cityId, days.value).then(d => {
    weatherHistory.value = d.history || []
  }).catch(() => { weatherHistory.value = [] })
}

function onDaysChange() { loadData() }
function onCityChange(cityId) {
  cityStore.selectCity(cityId)
}

watch(() => cityStore.currentCityId, () => loadData())

onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  if (!cityStore.currentCityId && cityStore.cities.length > 0) {
    cityStore.selectCity(cityStore.cities[0].id)
  }
  loadData()
})
</script>

<style scoped>
.analysis-page {
  min-height: 100vh;
  background: var(--bg-page);
  color: var(--text-primary);
}
.analysis-content { padding: 0 24px 24px; }

.analysis-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 12px;
}
.toolbar-left { display: flex; align-items: center; gap: 10px; }
.toolbar-title { font-size: 18px; font-weight: 700; }

.row-asymmetric {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}
.flex-grow { min-width: 0; }
.flex-side { min-width: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.stat-item { text-align: center; }
.stat-val {
  font-size: 24px;
  font-weight: 800;
  font-family: var(--font-mono);
}
.stat-val small { font-size: 12px; font-weight: 400; color: var(--text-muted); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
</style>
