<template>
  <div class="analysis-page">
    <AppHeader @city-change="onCityChange" />

    <div class="analysis-content">
      <div class="analysis-toolbar">
        <div class="toolbar-left">
          <Icon icon="mdi:chart-areaspline" width="22" style="color: var(--primary)" />
          <span class="toolbar-title">数据分析</span>
          <el-tag effect="plain" size="small">{{ selectedCityName }}</el-tag>
        </div>
        <div class="toolbar-right">
          <el-select v-model="selectedMetric" size="small" style="width: 120px" @change="loadData">
            <el-option label="AQI" value="aqi" />
            <el-option label="PM2.5" value="pm25" />
            <el-option label="PM10" value="pm10" />
            <el-option label="O3" value="o3" />
          </el-select>
          <el-select v-model="selectedAlgorithm" size="small" style="width: 140px" @change="loadData">
            <el-option label="移动平均" value="moving_average" />
            <el-option label="ARIMA" value="arima" />
            <el-option label="LSTM" value="lstm" />
          </el-select>
          <el-radio-group v-model="days" size="small" @change="onDaysChange">
            <el-radio-button :value="30">近30天</el-radio-button>
            <el-radio-button :value="60">近60天</el-radio-button>
            <el-radio-button :value="90">近90天</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div class="row-asymmetric">
        <el-card class="flex-grow">
          <template #header>
            <div class="card-header">
              <span>{{ metricLabel }} 走势与预测</span>
              <el-tag size="small" effect="plain" type="warning">{{ algorithmLabel }} + 模型评估</el-tag>
            </div>
          </template>
          <TrendLine
            :trend-data="aqStore.trendWithPrediction"
            :title="`${selectedCityName} ${metricLabel} 走势`"
            :metric="metricLabel"
            :algorithm-label="`${algorithmLabel}预测`"
            :reference-label="referenceLabel"
            height="340px"
          />
        </el-card>
        <el-card class="flex-side">
          <template #header><span>综合风险评分</span></template>
          <div v-if="aqStore.riskResult" class="risk-card-body">
            <div class="risk-score" :class="`risk-${aqStore.riskResult.level}`">{{ aqStore.riskResult.score }}</div>
            <div class="risk-level">{{ riskLevelText(aqStore.riskResult.level) }}</div>
            <div class="risk-summary">{{ aqStore.riskResult.summary }}</div>
            <div class="risk-drivers">
              <div v-for="item in (aqStore.riskResult.drivers || []).slice(0, 4)" :key="item.factor" class="risk-driver">
                <span>{{ item.factor.toUpperCase() }}</span>
                <span>{{ item.contribution }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无风险数据" :image-size="60" />
        </el-card>
      </div>

      <div class="row-asymmetric">
        <el-card class="flex-grow">
          <template #header>
            <div class="card-header">
              <span>模型准确性对比</span>
              <el-tag size="small" effect="plain" type="success">MAE / RMSE / MAPE / R²</el-tag>
            </div>
          </template>
          <el-table :data="aqStore.predictionResult?.comparison || []" stripe size="small">
            <el-table-column prop="algorithm" label="算法" min-width="120">
              <template #default="{ row }">{{ algorithmText(row.algorithm) }}</template>
            </el-table-column>
            <el-table-column prop="mae" label="MAE" min-width="90" />
            <el-table-column prop="rmse" label="RMSE" min-width="90" />
            <el-table-column prop="mape" label="MAPE" min-width="90" />
            <el-table-column prop="r2" label="R²" min-width="90" />
            <el-table-column prop="usedFallback" label="回退" min-width="80">
              <template #default="{ row }">
                <el-tag :type="row.usedFallback ? 'warning' : 'success'" size="small">{{ row.usedFallback ? '是' : '否' }}</el-tag>
              </template>
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

      <div class="row-asymmetric">
        <el-card class="flex-grow" v-if="aqStore.anomalyResult">
          <template #header><span>IQR 异常检测</span></template>
          <el-row :gutter="16">
            <el-col :span="6"><el-statistic title="数据点" :value="aqStore.anomalyResult.total_points" /></el-col>
            <el-col :span="6"><el-statistic title="异常数" :value="aqStore.anomalyResult.anomaly_count" /></el-col>
            <el-col :span="6"><el-statistic title="Q1 ~ Q3" :value="`${aqStore.anomalyResult.q1} ~ ${aqStore.anomalyResult.q3}`" /></el-col>
            <el-col :span="6"><el-statistic title="正常范围" :value="`${aqStore.anomalyResult.lower_bound} ~ ${aqStore.anomalyResult.upper_bound}`" /></el-col>
          </el-row>
          <el-table v-if="aqStore.anomalyResult.anomalies?.length > 0" :data="aqStore.anomalyResult.anomalies.slice(0, 10)" stripe size="small" style="margin-top: 16px" max-height="200">
            <el-table-column prop="date" label="日期" width="110" />
            <el-table-column prop="value" :label="metricLabel" width="90" />
            <el-table-column prop="type" label="方向" width="80">
              <template #default="{ row }"><el-tag :type="row.type === 'high' ? 'danger' : 'primary'" size="small">{{ row.type === 'high' ? '偏高' : '偏低' }}</el-tag></template>
            </el-table-column>
            <el-table-column prop="severity" label="程度">
              <template #default="{ row }"><el-tag :type="row.severity === 'severe' ? 'danger' : row.severity === 'moderate' ? 'warning' : 'info'" size="small">{{ { severe: '严重', moderate: '中度', mild: '轻度' }[row.severity] }}</el-tag></template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card class="flex-side">
          <template #header><span>未来 5 天风险</span></template>
          <div v-if="aqStore.riskResult?.futureRisk?.length" class="future-risk-list">
            <div v-for="item in aqStore.riskResult.futureRisk" :key="item.date" class="future-risk-item">
              <span>{{ item.date }}</span>
              <el-tag size="small" :type="riskTagType(item.level)">{{ riskLevelText(item.level) }}</el-tag>
              <b>{{ item.score }}</b>
            </div>
          </div>
          <el-empty v-else description="暂无未来风险数据" :image-size="60" />
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
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const cityStore = useCityStore()
const aqStore = useAirQualityStore()

const days = ref(60)
const realHistory = ref([])
const weatherHistory = ref([])
const selectedMetric = ref('aqi')
const selectedAlgorithm = ref('moving_average')

const selectedCityName = computed(() => cityStore.currentCity?.name || '全国')
const metricLabel = computed(() => ({ aqi: 'AQI', pm25: 'PM2.5', pm10: 'PM10', o3: 'O3' }[selectedMetric.value] || selectedMetric.value.toUpperCase()))
const algorithmLabel = computed(() => algorithmText(selectedAlgorithm.value))
const referenceLabel = computed(() => selectedAlgorithm.value === 'moving_average' ? '移动平均' : '历史拟合')

const pollutantLineOption = computed(() => {
  const h = realHistory.value
  if (!h.length) return {}
  const dates = h.map(r => r.date)
  const make = (key, name, color) => ({ name, type: 'line', data: h.map(r => r[key]), smooth: true, symbol: 'none', lineStyle: { width: 1.5, color }, itemStyle: { color } })
  return {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { fontSize: 11 } },
    grid: { left: 50, right: 16, top: 36, bottom: 45 },
    xAxis: { type: 'category', data: dates, axisLabel: { rotate: 35, fontSize: 10, formatter: v => v.slice(5) } },
    yAxis: { type: 'value' },
    series: [make('pm25', 'PM2.5', '#0d9488'), make('pm10', 'PM10', '#0891b2'), make('so2', 'SO₂', '#7c3aed'), make('no2', 'NO₂', '#e07a5f'), make('co', 'CO', '#d97706'), make('o3', 'O₃', '#059669')],
  }
})

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
    yAxis: [{ type: 'value', name: '℃', position: 'left' }, { type: 'value', name: 'mm', position: 'right', splitLine: { show: false } }],
    series: [
      { name: '温度', type: 'line', data: temps, smooth: true, symbol: 'none', lineStyle: { color: '#dc2626' }, itemStyle: { color: '#dc2626' } },
      { name: '降水', type: 'bar', data: rain, yAxisIndex: 1, barWidth: '40%', itemStyle: { color: 'rgba(13,148,136,0.4)' } },
    ],
  }
})

const historyStats = computed(() => {
  const h = realHistory.value
  if (!h?.length) return null
  const metricMap = { aqi: 'aqi', pm25: 'pm25', pm10: 'pm10', o3: 'o3' }
  const targetArr = h.map(r => r[metricMap[selectedMetric.value]]).filter(Boolean)
  const aqiArr = h.map(r => r.aqi).filter(Boolean)
  const avg = arr => (arr.reduce((s, v) => s + v, 0) / arr.length).toFixed(1)
  const goodDays = aqiArr.filter(v => v <= 100).length
  return [
    { label: `${metricLabel.value}均值`, value: avg(targetArr), color: 'var(--primary)' },
    { label: `${metricLabel.value}峰值`, value: Math.max(...targetArr), color: 'var(--danger)' },
    { label: `${metricLabel.value}最低`, value: Math.min(...targetArr), color: 'var(--success)' },
    { label: '优良天数', value: goodDays, suffix: ' 天', color: 'var(--success)' },
  ]
})

async function loadData() {
  const cityId = cityStore.currentCityId
  if (!cityId) return
  await Promise.all([
    aqStore.fetchLatest(),
    aqStore.fetchPrediction(cityId, selectedMetric.value, 7, 5, selectedAlgorithm.value, true),
    aqStore.fetchAnomalyDetect(cityId, selectedMetric.value),
    aqStore.fetchRiskAssess(cityId, 5),
  ])
  realAqiApi.getHistory(cityId, days.value).then(d => { realHistory.value = d.history || [] }).catch(() => { realHistory.value = [] })
  weatherApi.getHistory(cityId, days.value).then(d => { weatherHistory.value = d.history || [] }).catch(() => { weatherHistory.value = [] })
}

function onDaysChange() { loadData() }
function onCityChange(cityId) { cityStore.selectCity(cityId) }
function algorithmText(value) { return ({ moving_average: '移动平均', arima: 'ARIMA', lstm: 'LSTM' }[value] || value) }
function riskLevelText(level) { return ({ low: '低风险', medium: '中风险', high: '高风险', severe: '极高风险' }[level] || level) }
function riskTagType(level) { return ({ low: 'success', medium: 'warning', high: 'danger', severe: 'danger' }[level] || 'info') }

watch(() => cityStore.currentCityId, () => loadData())
onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  if (!cityStore.currentCityId && cityStore.cities.length > 0) cityStore.selectCity(cityStore.cities[0].id)
  loadData()
})
</script>

<style scoped>
.analysis-page { min-height: 100vh; background: var(--bg-page); color: var(--text-primary); }
.analysis-content { padding: 0 24px 24px; }
.analysis-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 0 12px; gap: 12px; }
.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.toolbar-title { font-size: 18px; font-weight: 700; }
.row-asymmetric { display: grid; grid-template-columns: 1.6fr 1fr; gap: 12px; margin-bottom: 12px; }
.flex-grow, .flex-side { min-width: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.stat-item { text-align: center; }
.stat-val { font-size: 24px; font-weight: 800; font-family: var(--font-mono); }
.stat-val small { font-size: 12px; font-weight: 400; color: var(--text-muted); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.risk-card-body { display: flex; flex-direction: column; gap: 10px; }
.risk-score { font-size: 42px; font-weight: 800; font-family: var(--font-mono); }
.risk-level { font-size: 18px; font-weight: 700; }
.risk-summary { font-size: 13px; color: var(--text-secondary); line-height: 1.7; }
.risk-drivers { display: grid; gap: 8px; }
.risk-driver { display: flex; justify-content: space-between; font-size: 12px; padding: 8px 10px; background: rgba(13,148,136,0.06); border-radius: 10px; }
.risk-low { color: #2d6a4f; }
.risk-medium { color: #d4a373; }
.risk-high { color: #c1121f; }
.risk-severe { color: #780116; }
.future-risk-list { display: grid; gap: 8px; }
.future-risk-item { display: grid; grid-template-columns: 1fr auto auto; gap: 8px; align-items: center; padding: 8px 10px; border-radius: 10px; background: rgba(224,122,95,0.06); font-size: 12px; }
</style>
