<template>
  <div class="analysis-page">
    <AppHeader @city-change="onCityChange" />

    <div class="analysis-content">
      <div class="analysis-toolbar">
        <div class="toolbar-left">
          <Icon icon="mdi:chart-areaspline" width="22" style="color: var(--primary)" />
          <span class="toolbar-title">数据分析</span>
          <span class="brand-date">({{ currentDate }})</span>
          <el-tag effect="plain" size="small">{{ selectedCityName }}</el-tag>
        </div>
        <div class="toolbar-right">
          <el-select v-model="selectedMetric" size="small" style="width: 120px" @change="loadData">
            <el-option label="AQI" value="aqi" />
            <el-option label="PM2.5" value="pm25" />
            <el-option label="PM10" value="pm10" />
            <el-option label="O3" value="o3" />
          </el-select>
          <el-select v-model="selectedAlgorithm" size="small" style="width: 160px" @change="loadData">
            <el-option v-for="item in algorithmOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
          <el-select v-model="selectedAnomalyMethod" size="small" style="width: 140px" @change="loadData">
            <el-option label="IQR" value="iqr" />
            <el-option label="Z-score" value="zscore" />
            <el-option label="MAD" value="mad" />
          </el-select>
          <el-radio-group v-model="days" size="small" @change="onDaysChange">
            <el-radio-button :value="30">近30天</el-radio-button>
            <el-radio-button :value="60">近60天</el-radio-button>
            <el-radio-button :value="90">近90天</el-radio-button>
          </el-radio-group>
        </div>
      </div>

      <div class="meta-row">
        <el-alert
          :title="predictionNotice"
          :type="aqStore.predictionMeta?.usedFallback ? 'warning' : 'info'"
          :closable="false"
          show-icon
        />
        <div class="meta-tags">
          <el-tag size="small" effect="plain">历史区间: {{ predictionRangeText }}</el-tag>
          <el-tag size="small" effect="plain">预测源: 本地数据库日均值</el-tag>
          <el-tag size="small" effect="plain" type="success">最佳算法: {{ bestAlgorithmLabel }}</el-tag>
        </div>
      </div>

      <div class="row-asymmetric">
        <el-card class="flex-grow">
          <template #header>
            <div class="card-header">
              <span>{{ metricLabel }} 走势与预测</span>
              <div class="header-tags">
                <el-tag size="small" effect="plain" type="warning">{{ algorithmLabel }}预测</el-tag>
                <el-tag size="small" effect="plain" type="success">预测均值 {{ predictionSummary.avg }}</el-tag>
                <el-tag size="small" effect="plain" type="danger">峰值 {{ predictionSummary.max }}</el-tag>
              </div>
            </div>
          </template>
          <TrendLine
            :trend-data="trimmedTrend"
            :title="`${selectedCityName} ${metricLabel} 走势`"
            :metric="metricLabel"
            :algorithm-label="`${algorithmLabel}预测`"
            :reference-label="referenceLabel"
            height="340px"
          />
          <div class="forecast-chip-row" v-if="forecastValueChips.length">
            <div v-for="item in forecastValueChips" :key="item.date" class="forecast-chip">
              <span>{{ item.date }}</span>
              <b>{{ item.value }}</b>
            </div>
          </div>
        </el-card>
        <el-card class="flex-side">
          <template #header><span>综合风险评分</span></template>
          <div v-if="aqStore.riskResult" class="risk-card-body">
            <div class="risk-score" :class="`risk-${aqStore.riskResult.level}`">{{ aqStore.riskResult.score }}</div>
            <div class="risk-level">{{ riskLevelText(aqStore.riskResult.level) }}</div>
            <div class="risk-summary">{{ aqStore.riskResult.summary }}</div>
            <div class="risk-components">
              <div class="risk-component"><span>污染暴露</span><b>{{ aqStore.riskResult.components?.pollution ?? '--' }}</b></div>
              <div class="risk-component"><span>扩散条件</span><b>{{ aqStore.riskResult.components?.diffusion ?? '--' }}</b></div>
              <div class="risk-component"><span>异常波动</span><b>{{ aqStore.riskResult.components?.anomaly ?? '--' }}</b></div>
              <div class="risk-component"><span>未来趋势</span><b>{{ aqStore.riskResult.components?.forecast ?? '--' }}</b></div>
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
              <div class="header-actions">
                <el-tag size="small" effect="plain" type="success">MAE / RMSE / MAPE / R²</el-tag>
                <el-button size="small" plain :disabled="!comparisonRows.length" @click="exportComparisonCSV">Export CSV</el-button>
              </div>
            </div>
          </template>
          <el-table :data="comparisonRows" stripe size="small">
            <el-table-column prop="algorithm" label="算法" min-width="150">
              <template #default="{ row }">{{ row.algorithmLabel }}</template>
            </el-table-column>
            <el-table-column prop="mae" label="MAE" min-width="90" />
            <el-table-column prop="rmse" label="RMSE" min-width="90" />
            <el-table-column prop="mape" label="MAPE" min-width="90" />
            <el-table-column prop="r2" label="R²" min-width="90" />
            <el-table-column prop="status" label="状态" min-width="110">
              <template #default="{ row }">
                <el-tag :type="row.usedFallback ? 'warning' : 'success'" size="small">{{ row.statusLabel }}</el-tag>
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
              <span>数据库最新值 vs Open-Meteo 实时值</span>
              <el-tag size="small" effect="plain" :type="realtimeDiffType">{{ realtimeDiffText }}</el-tag>
            </div>
          </template>
          <el-table :data="realtimeCompareRows" stripe size="small">
            <el-table-column prop="name" label="指标" min-width="120" />
            <el-table-column prop="dbValue" label="数据库最新值" min-width="120" />
            <el-table-column prop="realValue" label="实时值" min-width="120" />
            <el-table-column prop="diff" label="差值" min-width="100" />
          </el-table>
          <div class="source-note">数据库值来自 latest 接口聚合日均值；实时值来自 Open-Meteo 接口，口径不同会导致差异。</div>
        </el-card>
        <el-card class="flex-side">
          <template #header>
            <div class="card-header">
              <span>算法可用状态</span>
              <el-tag size="small" effect="plain">当前: {{ algorithmLabel }}</el-tag>
            </div>
          </template>
          <div class="availability-list">
            <div v-for="item in availabilityList" :key="item.key" class="availability-item">
              <span>{{ item.label }}</span>
              <el-tag size="small" :type="item.available ? 'success' : 'warning'">{{ item.available ? '可用' : '缺依赖/回退' }}</el-tag>
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
          <EChartWrapper v-if="realHistory.length" :option="pollutantLineOption" height="300px" />
          <el-empty v-else description="真实空气质量历史暂不可用" :image-size="60" />
        </el-card>
        <el-card class="flex-side">
          <template #header>
            <div class="card-header">
              <span>气温与降水 (近{{ days }}天)</span>
              <el-tag size="small" effect="plain" type="success">真实数据</el-tag>
            </div>
          </template>
          <EChartWrapper v-if="weatherHistory.length" :option="weatherChartOption" height="300px" />
          <el-empty v-else description="历史天气暂不可用" :image-size="60" />
        </el-card>
      </div>

      <div class="row-asymmetric">
        <el-card class="flex-grow" v-if="aqStore.anomalyResult">
          <template #header>
            <div class="card-header">
              <span>{{ anomalyMethodLabel }} 异常检测</span>
              <el-tag size="small" effect="plain">多方法对比</el-tag>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="6"><el-statistic title="数据点" :value="aqStore.anomalyResult.total_points" /></el-col>
            <el-col :span="6"><el-statistic title="异常数" :value="aqStore.anomalyResult.anomaly_count" /></el-col>
            <el-col :span="6"><el-statistic title="当前方法" :value="anomalyMethodLabel" /></el-col>
            <el-col :span="6"><el-statistic title="异常占比" :value="anomalyRatio" suffix="%" /></el-col>
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
          <el-empty v-else description="暂无异常数据" :image-size="60" />
        </el-card>

        <el-card class="flex-side">
          <template #header><span>异常方法对比</span></template>
          <div class="future-risk-list">
            <div v-for="item in aqStore.anomalyResult?.comparison || []" :key="item.method" class="future-risk-item">
              <span>{{ anomalyMethodText(item.method) }}</span>
              <el-tag size="small" type="info">{{ item.anomalyCount }} 个</el-tag>
            </div>
          </div>
          <div class="risk-basis" v-if="aqStore.riskResult?.basis?.length">
            <div class="basis-title">评分依据</div>
            <div v-for="item in aqStore.riskResult.basis" :key="item" class="basis-item">{{ item }}</div>
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
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const cityStore = useCityStore()
const aqStore = useAirQualityStore()

const days = ref(60)
const realHistory = ref([])
const weatherHistory = ref([])
const selectedMetric = ref('aqi')
const selectedAlgorithm = ref('moving_average')
const selectedAnomalyMethod = ref('iqr')

const algorithmOptions = [
  { label: '移动平均', value: 'moving_average' },
  { label: '加权移动平均', value: 'weighted_moving_average' },
  { label: '线性回归', value: 'linear_regression' },
  { label: 'Holt-Winters', value: 'holt_winters' },
  { label: 'ARIMA', value: 'arima' },
  { label: 'LSTM', value: 'lstm' },
]
const currentDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`
})

const selectedCityName = computed(() => cityStore.currentCity?.name || '全国')
const latestCity = computed(() => aqStore.latestData.find((d) => d.cityId === cityStore.currentCityId) || null)
const metricLabel = computed(() => ({ aqi: 'AQI', pm25: 'PM2.5', pm10: 'PM10', o3: 'O3' }[selectedMetric.value] || selectedMetric.value.toUpperCase()))
const algorithmLabel = computed(() => algorithmText(selectedAlgorithm.value))
const anomalyMethodLabel = computed(() => anomalyMethodText(selectedAnomalyMethod.value))
const referenceLabel = computed(() => aqStore.predictionMeta?.referenceLabel || '参考线')

// 截断趋势图历史部分，只显示近 days 天 + 预测
const trimmedTrend = computed(() => {
  const full = aqStore.trendWithPrediction
  if (!full || !full.dates || full.dates.length === 0) return full
  // 找到历史与预测的分界点（第一个 predicted 非 null 的位置）
  let splitIdx = full.predicted.findIndex((v) => v != null)
  if (splitIdx < 0) splitIdx = full.dates.length
  // 历史部分只取最后 days 天
  const historyStart = Math.max(0, splitIdx - days.value)
  const trimmedDates = [...full.dates.slice(historyStart, splitIdx), ...full.dates.slice(splitIdx)]
  const trimmedActual = [...full.actual.slice(historyStart, splitIdx), ...full.actual.slice(splitIdx)]
  const trimmedRef = full.reference ? [...full.reference.slice(historyStart, splitIdx), ...full.reference.slice(splitIdx)] : undefined
  const trimmedPredicted = [...full.predicted.slice(historyStart, splitIdx), ...full.predicted.slice(splitIdx)]
  const trimmedUpper = [...full.upper.slice(historyStart, splitIdx), ...full.upper.slice(splitIdx)]
  const trimmedLower = [...full.lower.slice(historyStart, splitIdx), ...full.lower.slice(splitIdx)]
  return {
    dates: trimmedDates,
    actual: trimmedActual,
    reference: trimmedRef,
    predicted: trimmedPredicted,
    upper: trimmedUpper,
    lower: trimmedLower,
  }
})

const bestAlgorithmLabel = computed(() => algorithmText(aqStore.predictionMeta?.bestAlgorithm || aqStore.predictionMeta?.selectedAlgorithm || selectedAlgorithm.value))
const predictionRangeText = computed(() => {
  const meta = aqStore.predictionMeta
  if (!meta?.historyStart || !meta?.historyEnd) return '--'
  return `${meta.historyStart} ~ ${meta.historyEnd} (${meta.historyDays}天)`
})
const predictionNotice = computed(() => {
  const meta = aqStore.predictionMeta
  if (!meta) return '暂无预测结果'
  if (meta.usedFallback) return `当前请求算法为 ${algorithmText(meta.requestedAlgorithm)}，但由于 ${meta.fallbackReason}，系统已回退到 ${algorithmText(meta.selectedAlgorithm)}。`
  return `当前使用 ${algorithmText(meta.selectedAlgorithm)}；历史区间 ${predictionRangeText.value}；最佳算法建议为 ${bestAlgorithmLabel.value}。`
})
const availabilityList = computed(() => Object.entries(aqStore.predictionMeta?.availability || {}).map(([key, value]) => ({ key, label: algorithmText(key), available: value.available, reason: value.reason })))
const comparisonRows = computed(() => (aqStore.predictionResult?.comparison || []).map((row) => ({
  ...row,
  algorithmLabel: algorithmText(row.algorithm),
  status: row.usedFallback ? 'fallback' : 'normal',
  statusLabel: row.usedFallback ? '回退' : '正常',
})))

const realtimeCompareRows = computed(() => {
  const dbRow = latestCity.value
  const rt = aqStore.realtimeLatest
  if (!dbRow || !rt?.source) return []
  return [
    { name: 'AQI', dbValue: dbRow.aqi ?? '--', realValue: rt.aqi ?? '--', diff: diffText(dbRow.aqi, rt.aqi) },
    { name: 'PM2.5', dbValue: dbRow.pm25 ?? '--', realValue: rt.pm25 ?? '--', diff: diffText(dbRow.pm25, rt.pm25) },
    { name: 'PM10', dbValue: dbRow.pm10 ?? '--', realValue: rt.pm10 ?? '--', diff: diffText(dbRow.pm10, rt.pm10) },
    { name: 'O₃', dbValue: dbRow.o3 ?? '--', realValue: rt.o3 ?? '--', diff: diffText(dbRow.o3, rt.o3) },
  ]
})
const realtimeDiffType = computed(() => {
  const first = realtimeCompareRows.value[0]
  if (!first || first.diff === '--') return 'info'
  return Math.abs(Number(first.diff)) >= 30 ? 'warning' : 'success'
})
const realtimeDiffText = computed(() => {
  if (!realtimeCompareRows.value.length) return '暂无实时对照'
  return '数据库值与实时值口径可能存在差异'
})

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
  const targetArr = h.map(r => r[metricMap[selectedMetric.value]]).filter(v => v != null)
  const aqiArr = h.map(r => r.aqi).filter(v => v != null)
  if (!targetArr.length) return null
  const avg = arr => (arr.reduce((s, v) => s + v, 0) / arr.length).toFixed(1)
  const goodDays = aqiArr.filter(v => v <= 100).length
  return [
    { label: `${metricLabel.value}均值`, value: avg(targetArr), color: 'var(--primary)' },
    { label: `${metricLabel.value}峰值`, value: Math.max(...targetArr), color: 'var(--danger)' },
    { label: `${metricLabel.value}最低`, value: Math.min(...targetArr), color: 'var(--success)' },
    { label: '优良天数', value: goodDays, suffix: ' 天', color: 'var(--success)' },
  ]
})

const forecastValueChips = computed(() => (aqStore.predictionResult?.predictions || []).slice(0, 5).map(item => ({
  date: item.date?.slice(5) || '--',
  value: item.predicted ?? '--',
})))

const predictionSummary = computed(() => {
  const values = (aqStore.predictionResult?.predictions || []).map(item => item.predicted).filter(v => v != null)
  if (!values.length) return { avg: '--', max: '--' }
  const avg = (values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1)
  const max = Math.max(...values).toFixed(1)
  return { avg, max }
})

const anomalyRatio = computed(() => {
  const r = aqStore.anomalyResult
  if (!r || !r.total_points) return 0
  return ((r.anomaly_count / r.total_points) * 100).toFixed(1)
})

async function loadData() {
  const cityId = cityStore.currentCityId
  if (!cityId) return
  await aqStore.fetchLatest()
  await Promise.allSettled([
    aqStore.fetchRealtimeLatest(cityId),
    aqStore.fetchPrediction(cityId, selectedMetric.value, 7, 5, selectedAlgorithm.value, true),
    aqStore.fetchAnomalyDetect(cityId, selectedMetric.value, days.value, selectedAnomalyMethod.value, true),
    aqStore.fetchRiskAssess(cityId, 5),
    realAqiApi.getHistory(cityId, days.value).then(d => { realHistory.value = d.history || realHistory.value }).catch(() => realHistory.value),
    weatherApi.getHistory(cityId, days.value).then(d => { weatherHistory.value = d.history || weatherHistory.value }).catch(() => weatherHistory.value),
  ])
}

function onDaysChange() { loadData() }
function onCityChange(cityId) { cityStore.selectCity(cityId) }
function algorithmText(value) {
  return ({
    moving_average: '移动平均',
    weighted_moving_average: '加权移动平均',
    linear_regression: '线性回归',
    holt_winters: 'Holt-Winters',
    arima: 'ARIMA',
    lstm: 'LSTM',
  }[value] || value)
}
function anomalyMethodText(value) { return ({ iqr: 'IQR', zscore: 'Z-score', mad: 'MAD' }[value] || value) }
function riskLevelText(level) { return ({ low: '低风险', medium: '中风险', high: '高风险', severe: '极高风险' }[level] || level) }
function diffText(dbValue, realValue) {
  if (dbValue == null || realValue == null) return '--'
  return (Number(dbValue) - Number(realValue)).toFixed(1)
}
function escapeCSVCell(value) {
  const text = value == null ? '' : String(value)
  if (/[",\n\r]/.test(text)) return `"${text.replace(/"/g, '""')}"`
  return text
}
function formatTimestamp(date = new Date()) {
  const pad = (v) => String(v).padStart(2, '0')
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}_${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`
}
function exportComparisonCSV() {
  if (!comparisonRows.value.length) return

  const exportTime = new Date().toISOString()
  const headers = ['cityName', 'metric', 'algorithm', 'mae', 'rmse', 'mape', 'r2', 'available', 'usedFallback', 'status', 'bestAlgorithm', 'exportTime']
  const rows = comparisonRows.value.map((row) => ([
    selectedCityName.value,
    selectedMetric.value,
    row.algorithm,
    row.mae ?? '',
    row.rmse ?? '',
    row.mape ?? '',
    row.r2 ?? '',
    row.available ?? '',
    row.usedFallback ?? '',
    row.status,
    aqStore.predictionMeta?.bestAlgorithm || '',
    exportTime,
  ]))
  const csv = '\uFEFF' + [headers, ...rows].map((row) => row.map(escapeCSVCell).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `model_evaluation_${selectedCityName.value}_${selectedMetric.value}_${formatTimestamp()}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

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
.meta-row { display: grid; gap: 10px; margin-bottom: 12px; }
.meta-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.row-asymmetric { display: grid; grid-template-columns: 1.6fr 1fr; gap: 12px; margin-bottom: 12px; }
.flex-grow, .flex-side { min-width: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
.header-tags, .header-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.forecast-chip-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(88px, 1fr)); gap: 8px; margin-top: 12px; }
.forecast-chip { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px; border-radius: 10px; background: rgba(230, 162, 60, 0.08); font-size: 12px; }
.forecast-chip b { font-family: var(--font-mono); color: #c2410c; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.stat-item { text-align: center; }
.stat-val { font-size: 24px; font-weight: 800; font-family: var(--font-mono); }
.stat-val small { font-size: 12px; font-weight: 400; color: var(--text-muted); }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }
.risk-card-body { display: flex; flex-direction: column; gap: 10px; }
.risk-score { font-size: 42px; font-weight: 800; font-family: var(--font-mono); }
.risk-level { font-size: 18px; font-weight: 700; }
.risk-summary { font-size: 13px; color: var(--text-secondary); line-height: 1.7; }
.risk-components { display: grid; gap: 8px; }
.risk-component, .availability-item { display: flex; justify-content: space-between; align-items: center; font-size: 12px; padding: 8px 10px; background: rgba(13,148,136,0.06); border-radius: 10px; }
.risk-low { color: #2d6a4f; }
.risk-medium { color: #d4a373; }
.risk-high { color: #c1121f; }
.risk-severe { color: #780116; }
.future-risk-list, .availability-list { display: grid; gap: 8px; }
.future-risk-item { display: grid; grid-template-columns: 1fr auto auto; gap: 8px; align-items: center; padding: 8px 10px; border-radius: 10px; background: rgba(224,122,95,0.06); font-size: 12px; }
.source-note { font-size: 12px; color: var(--text-muted); margin-top: 8px; }
.risk-basis { margin-top: 12px; display: grid; gap: 8px; }
.basis-title { font-size: 13px; font-weight: 700; }
.basis-item { font-size: 12px; line-height: 1.6; color: var(--text-secondary); }
:deep(.el-alert){
  background-color: #11111f;

}
</style>