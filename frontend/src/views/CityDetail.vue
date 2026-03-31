<template>
  <div class="city-detail">
    <AppHeader @city-change="onCityChange" />

    <div class="detail-content" v-loading="loading">
      <el-page-header @back="$router.push('/')" style="padding: 16px 24px 0">
        <template #content>
          <span class="page-title">{{ city?.name }} 空气质量详情</span>
        </template>
      </el-page-header>

      <div class="kpi-row" v-if="latestCity">
        <div class="kpi-hero" :style="{ borderLeftColor: aqiColor(latestCity.aqi) }">
          <div class="kpi-big" :style="{ color: aqiColor(latestCity.aqi) }">{{ latestCity.aqi }}</div>
          <div class="kpi-sub">AQI · {{ latestCity.qualityLevel }}</div>
          <div class="kpi-tip">数据库日期: {{ latestCity.recordDate || '--' }}</div>
          <div class="kpi-tip">数据来源: {{ latestCity.dataSource || 'local_db_daily_avg' }}</div>
        </div>
        <div class="kpi-grid">
          <div class="kpi-card"><div class="kpi-num">{{ latestCity.pm25 }}</div><div class="kpi-sub">PM2.5</div></div>
          <div class="kpi-card"><div class="kpi-num">{{ latestCity.pm10 }}</div><div class="kpi-sub">PM10</div></div>
          <div class="kpi-card"><div class="kpi-num">{{ latestCity.so2 }}</div><div class="kpi-sub">SO₂</div></div>
          <div class="kpi-card"><div class="kpi-num">{{ latestCity.no2 }}</div><div class="kpi-sub">NO₂</div></div>
          <div class="kpi-card"><div class="kpi-num">{{ latestCity.co }}</div><div class="kpi-sub">CO</div></div>
          <div class="kpi-card"><div class="kpi-num">{{ latestCity.o3 }}</div><div class="kpi-sub">O₃</div></div>
        </div>
      </div>

      <el-alert
        :title="predictionNotice"
        :type="aqStore.predictionMeta?.usedFallback ? 'warning' : 'info'"
        :closable="false"
        show-icon
        style="margin: 0 24px 12px"
      />

      <HealthAdvice
        v-if="latestCity"
        :aqi="latestCity.aqi"
        :quality-level="latestCity.qualityLevel"
        :risk-level="aqStore.riskResult?.level"
        :future-summary="aqStore.riskResult?.summary"
        :main-pollutants="(aqStore.riskResult?.drivers || []).slice(0, 3).map(d => d.factor)"
        style="margin: 0 24px"
      />

      <el-card style="margin: 8px 24px" v-if="aqStore.riskResult">
        <template #header>
          <div class="card-header">
            <span>综合风险评分</span>
            <el-tag :type="riskTagType(aqStore.riskResult.level)">{{ riskLevelText(aqStore.riskResult.level) }}</el-tag>
          </div>
        </template>
        <div class="risk-panel">
          <div class="risk-score" :style="{ color: riskColor(aqStore.riskResult.level) }">{{ aqStore.riskResult.score }}</div>
          <div class="risk-summary">{{ aqStore.riskResult.summary }}</div>
          <div class="risk-components">
            <div class="risk-driver"><span>污染暴露</span><b>{{ aqStore.riskResult.components?.pollution }}</b></div>
            <div class="risk-driver"><span>扩散条件</span><b>{{ aqStore.riskResult.components?.diffusion }}</b></div>
            <div class="risk-driver"><span>异常波动</span><b>{{ aqStore.riskResult.components?.anomaly }}</b></div>
            <div class="risk-driver"><span>未来趋势</span><b>{{ aqStore.riskResult.components?.forecast }}</b></div>
          </div>
          <div class="risk-basis">
            <div v-for="item in aqStore.riskResult.basis || []" :key="item" class="basis-item">{{ item }}</div>
          </div>
        </div>
      </el-card>

      <el-card style="margin: 0 24px 8px" v-if="aqStore.riskResult?.metricPredictions">
        <template #header>
          <div class="card-header">
            <span>未来 5 天多指标预测摘要</span>
            <el-tag size="small" effect="plain">{{ algorithmLabel }}</el-tag>
          </div>
        </template>
        <div class="multi-metric-grid">
          <div class="metric-forecast-card" v-for="metric in metricCards" :key="metric.key">
            <div class="metric-name">{{ metric.label }}</div>
            <div class="metric-values">
              <div v-for="item in metric.items" :key="item.date" class="metric-value-line">
                <span>{{ item.date.slice(5) }}</span>
                <b>{{ item.predicted }}</b>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card style="margin: 0 24px 12px">
        <template #header>
          <div class="card-header">
            <span>数据库值 vs 实时值</span>
            <el-tag size="small" effect="plain">Open-Meteo 对照</el-tag>
          </div>
        </template>
        <el-table :data="realtimeCompareRows" stripe size="small">
          <el-table-column prop="name" label="指标" />
          <el-table-column prop="dbValue" label="数据库最新值" />
          <el-table-column prop="realValue" label="实时值" />
          <el-table-column prop="diff" label="差值" />
        </el-table>
        <div class="tip-text">数据库值来自本地日均聚合；实时值来自 Open-Meteo，出现不一致属于数据口径差异，不是同一时间切片。</div>
      </el-card>

      <el-descriptions :column="5" border style="margin: 12px 24px" size="small">
        <el-descriptions-item label="省份">{{ city?.province }}</el-descriptions-item>
        <el-descriptions-item label="城市编码">{{ city?.cityCode }}</el-descriptions-item>
        <el-descriptions-item label="城市等级">{{ city?.cityLevel }}</el-descriptions-item>
        <el-descriptions-item label="常住人口">{{ city?.population ? city.population + ' 万' : '--' }}</el-descriptions-item>
        <el-descriptions-item label="监测站点">
          <el-tag v-for="s in stations" :key="s.id" size="small" class="station-tag">{{ s.stationName }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="charts-grid">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ metricLabel }} 走势 + 预测</span>
              <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                <el-select v-model="selectedMetric" size="small" style="width:110px" @change="loadFullData">
                  <el-option label="AQI" value="aqi" />
                  <el-option label="PM2.5" value="pm25" />
                  <el-option label="PM10" value="pm10" />
                  <el-option label="O3" value="o3" />
                </el-select>
                <el-select v-model="selectedAlgorithm" size="small" style="width:160px" @change="loadFullData">
                  <el-option v-for="item in algorithmOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
                <el-select v-model="selectedAnomalyMethod" size="small" style="width:140px" @change="loadFullData">
                  <el-option label="IQR" value="iqr" />
                  <el-option label="Z-score" value="zscore" />
                  <el-option label="MAD" value="mad" />
                </el-select>
                <el-radio-group v-model="days" size="small" @change="onDaysChange">
                  <el-radio-button :value="30">30天</el-radio-button>
                  <el-radio-button :value="60">60天</el-radio-button>
                  <el-radio-button :value="90">90天</el-radio-button>
                </el-radio-group>
              </div>
            </div>
          </template>
          <TrendLine :trend-data="combinedTrend" :title="`${city?.name || ''} ${metricLabel} 走势`" :metric="metricLabel" :algorithm-label="`${algorithmLabel}预测`" :reference-label="referenceLabel" height="350px" />
        </el-card>

        <el-card>
          <template #header><span>模型对比结果</span></template>
          <el-table :data="aqStore.predictionResult?.comparison || []" stripe size="small">
            <el-table-column prop="algorithm" label="算法">
              <template #default="{ row }">{{ algorithmText(row.algorithm) }}</template>
            </el-table-column>
            <el-table-column prop="mae" label="MAE" />
            <el-table-column prop="rmse" label="RMSE" />
            <el-table-column prop="mape" label="MAPE" />
            <el-table-column prop="r2" label="R²" />
            <el-table-column prop="usedFallback" label="状态">
              <template #default="{ row }"><el-tag :type="row.usedFallback ? 'warning' : 'success'" size="small">{{ row.usedFallback ? '回退' : '正常' }}</el-tag></template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <div class="charts-grid" style="margin-top: 0">
        <el-card>
          <template #header><span>达标了吗？</span></template>
          <el-table :data="pollutantTable" stripe size="small" style="width: 100%">
            <el-table-column prop="name" label="污染物" width="90" />
            <el-table-column prop="value" label="当前值" width="90">
              <template #default="{ row }"><span :style="{ color: row.value > row.limit ? 'var(--danger)' : 'var(--success)', fontWeight: 600 }">{{ row.value }}</span></template>
            </el-table-column>
            <el-table-column prop="unit" label="单位" width="80" />
            <el-table-column prop="limit" label="国标限值" width="90" />
            <el-table-column label="达标?" width="90">
              <template #default="{ row }"><el-tag :type="row.value <= row.limit ? 'success' : 'danger'" size="small">{{ row.value <= row.limit ? '达标' : '超了' }}</el-tag></template>
            </el-table-column>
            <el-table-column label="占比">
              <template #default="{ row }"><el-progress :percentage="Math.min(100, Math.round((row.value / row.limit) * 100))" :color="row.value > row.limit ? 'var(--danger)' : 'var(--success)'" :stroke-width="12" /></template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ anomalyMethodLabel }} 异常检测</span>
              <el-tag size="small" effect="plain">多方法对比</el-tag>
            </div>
          </template>
          <div v-if="aqStore.anomalyResult">
            <el-row :gutter="16">
              <el-col :span="8"><el-statistic title="数据点" :value="aqStore.anomalyResult.total_points" /></el-col>
              <el-col :span="8"><el-statistic title="异常数" :value="aqStore.anomalyResult.anomaly_count" /></el-col>
              <el-col :span="8"><el-statistic title="异常占比" :value="anomalyRatio" suffix="%" /></el-col>
            </el-row>
            <el-table v-if="aqStore.anomalyResult.anomalies?.length > 0" :data="aqStore.anomalyResult.anomalies" stripe size="small" style="margin-top: 12px" max-height="220">
              <el-table-column prop="date" label="日期" width="100" />
              <el-table-column prop="value" label="数值" width="80" />
              <el-table-column prop="type" label="方向" width="70">
                <template #default="{ row }"><el-tag :type="row.type === 'high' ? 'danger' : 'primary'" size="small">{{ row.type === 'high' ? '偏高' : '偏低' }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="severity" label="严重度">
                <template #default="{ row }"><el-tag :type="row.severity === 'severe' ? 'danger' : row.severity === 'moderate' ? 'warning' : 'info'" size="small">{{ { severe: '严重', moderate: '中度', mild: '轻度' }[row.severity] }}</el-tag></template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无异常数据" :image-size="60" />
            <div class="method-compare">
              <div v-for="item in aqStore.anomalyResult.comparison || []" :key="item.method" class="method-item">
                <span>{{ anomalyMethodText(item.method) }}</span>
                <b>{{ item.anomalyCount }}</b>
              </div>
            </div>
          </div>
        </el-card>
      </div>

      <el-card style="margin: 0 24px 24px" v-if="historyStats">
        <template #header><span>近{{ days }}天统计</span></template>
        <el-row :gutter="24">
          <el-col :span="4" v-for="stat in historyStats" :key="stat.label">
            <el-statistic :title="stat.label" :value="stat.value" :suffix="stat.suffix" :value-style="{ color: stat.color || '' }" />
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCityStore } from '@/stores/city'
import { useAirQualityStore } from '@/stores/airQuality'
import { cityApi } from '@/api/modules'
import AppHeader from '@/components/layout/AppHeader.vue'
import TrendLine from '@/components/charts/TrendLine.vue'
import HealthAdvice from '@/components/HealthAdvice.vue'

const route = useRoute()
const router = useRouter()
const cityStore = useCityStore()
const aqStore = useAirQualityStore()

const loading = ref(false)
const days = ref(60)
const city = ref(null)
const stations = ref([])
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

const metricLabel = computed(() => ({ aqi: 'AQI', pm25: 'PM2.5', pm10: 'PM10', o3: 'O3' }[selectedMetric.value] || selectedMetric.value.toUpperCase()))
const algorithmLabel = computed(() => algorithmText(selectedAlgorithm.value))
const anomalyMethodLabel = computed(() => anomalyMethodText(selectedAnomalyMethod.value))
const latestCity = computed(() => aqStore.latestData.find((d) => d.cityId === city.value?.id))
const combinedTrend = computed(() => aqStore.trendWithPrediction)
const referenceLabel = computed(() => aqStore.predictionMeta?.referenceLabel || '参考线')
const predictionNotice = computed(() => {
  const meta = aqStore.predictionMeta
  if (!meta) return '暂无预测结果'
  if (meta.usedFallback) return `当前请求算法为 ${algorithmText(meta.requestedAlgorithm)}，由于 ${meta.fallbackReason}，系统已回退到 ${algorithmText(meta.selectedAlgorithm)}。`
  return `当前使用 ${algorithmText(meta.selectedAlgorithm)}，历史区间 ${meta.historyStart || '--'} ~ ${meta.historyEnd || '--'}。`
})
const metricCards = computed(() => {
  const source = aqStore.riskResult?.metricPredictions || {}
  return [
    { key: 'aqi', label: 'AQI', items: (source.aqi || []).slice(0, 5) },
    { key: 'pm25', label: 'PM2.5', items: (source.pm25 || []).slice(0, 5) },
    { key: 'pm10', label: 'PM10', items: (source.pm10 || []).slice(0, 5) },
    { key: 'o3', label: 'O3', items: (source.o3 || []).slice(0, 5) },
  ]
})

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

const pollutantTable = computed(() => {
  const c = latestCity.value
  if (!c) return []
  return [
    { name: 'PM2.5', value: c.pm25, unit: 'μg/m³', limit: 75 },
    { name: 'PM10', value: c.pm10, unit: 'μg/m³', limit: 150 },
    { name: 'SO₂', value: c.so2, unit: 'μg/m³', limit: 60 },
    { name: 'NO₂', value: c.no2, unit: 'μg/m³', limit: 80 },
    { name: 'CO', value: c.co, unit: 'mg/m³', limit: 4 },
    { name: 'O₃', value: c.o3, unit: 'μg/m³', limit: 160 },
  ]
})

const anomalyRatio = computed(() => {
  const r = aqStore.anomalyResult
  if (!r || !r.total_points) return 0
  return ((r.anomaly_count / r.total_points) * 100).toFixed(1)
})

const historyStats = computed(() => {
  const h = aqStore.historyRecords
  if (!h || h.length === 0) return null
  const metricMap = { aqi: 'aqi', pm25: 'pm25', pm10: 'pm10', o3: 'o3' }
  const targetArr = h.map((r) => r[metricMap[selectedMetric.value]]).filter((v) => v != null)
  if (!targetArr.length) return null
  const avg = (arr) => (arr.reduce((s, v) => s + v, 0) / arr.length).toFixed(1)
  return [
    { label: `${metricLabel.value}均值`, value: avg(targetArr), color: 'var(--primary)' },
    { label: `${metricLabel.value}最高`, value: Math.max(...targetArr), color: 'var(--danger)' },
    { label: `${metricLabel.value}最低`, value: Math.min(...targetArr), color: 'var(--success)' },
  ]
})

async function loadFullData() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const detail = await cityApi.getDetail(id)
    city.value = detail
    stations.value = detail.stations || []
    cityStore.selectCity(id)
    await aqStore.fetchLatest()
    await Promise.allSettled([
      aqStore.fetchRealtimeLatest(id),
      aqStore.fetchHistory(id, days.value),
      aqStore.fetchPrediction(id, selectedMetric.value, 7, 5, selectedAlgorithm.value, true),
      aqStore.fetchAnomalyDetect(id, selectedMetric.value, 90, selectedAnomalyMethod.value, true),
      aqStore.fetchRiskAssess(id, 5),
    ])
  } finally {
    loading.value = false
  }
}

async function onDaysChange() {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    await aqStore.fetchHistory(id, days.value)
  } finally {
    loading.value = false
  }
}

function onCityChange(cityId) { router.push(`/city/${cityId}`) }
function aqiColor(aqi) { if (!aqi) return '#8a8a8a'; if (aqi <= 50) return '#2d6a4f'; if (aqi <= 100) return '#d4a373'; if (aqi <= 150) return '#e07a5f'; if (aqi <= 200) return '#c1121f'; return '#780116' }
function algorithmText(value) { return ({ moving_average: '移动平均', weighted_moving_average: '加权移动平均', linear_regression: '线性回归', holt_winters: 'Holt-Winters', arima: 'ARIMA', lstm: 'LSTM' }[value] || value) }
function anomalyMethodText(value) { return ({ iqr: 'IQR', zscore: 'Z-score', mad: 'MAD' }[value] || value) }
function riskLevelText(level) { return ({ low: '低风险', medium: '中风险', high: '高风险', severe: '极高风险' }[level] || level) }
function riskTagType(level) { return ({ low: 'success', medium: 'warning', high: 'danger', severe: 'danger' }[level] || 'info') }
function riskColor(level) { return ({ low: '#2d6a4f', medium: '#d4a373', high: '#c1121f', severe: '#780116' }[level] || '#2c2c2c') }
function diffText(dbValue, realValue) {
  if (dbValue == null || realValue == null) return '--'
  return (Number(dbValue) - Number(realValue)).toFixed(1)
}

watch(() => route.params.id, loadFullData)
onMounted(async () => { if (cityStore.cities.length === 0) await cityStore.fetchCities(); loadFullData() })
</script>

<style scoped>
.city-detail { min-height: 100vh; background: var(--bg-page, #eae6e1); color: var(--text-primary, #2c2c2c); }
.page-title { font-size: 16px; font-weight: 700; }
.station-tag { margin-right: 6px; }
.kpi-row { display: flex; gap: 16px; padding: 12px 24px; align-items: stretch; }
.kpi-hero { flex: 0 0 220px; background: var(--bg-card, rgba(255,255,255,0.85)); border-radius: 14px; padding: 16px 20px; border-left: 4px solid; box-shadow: var(--shadow); }
.kpi-big { font-size: 48px; font-weight: 800; line-height: 1.1; letter-spacing: -2px; }
.kpi-grid { flex: 1; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }
.kpi-card { background: var(--bg-card, rgba(255,255,255,0.85)); border-radius: 12px; padding: 12px 14px; text-align: left; box-shadow: var(--shadow); }
.kpi-num { font-size: 22px; font-weight: 700; }
.kpi-sub, .kpi-tip { font-size: 12px; color: var(--text-muted, #8a8a8a); margin-top: 4px; }
.card-header { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }
.risk-panel { display: grid; gap: 12px; }
.risk-score { font-size: 40px; font-weight: 800; font-family: var(--font-mono); }
.risk-summary, .tip-text { font-size: 13px; line-height: 1.7; color: var(--text-secondary); }
.risk-components, .risk-basis, .method-compare { display: grid; gap: 8px; }
.risk-driver, .method-item { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 8px 10px; border-radius: 10px; background: rgba(13,148,136,0.06); font-size: 12px; }
.basis-item { font-size: 12px; color: var(--text-secondary); line-height: 1.6; }
.multi-metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.metric-forecast-card { padding: 12px; border-radius: 12px; background: rgba(255,255,255,0.7); border: 1px solid var(--border-color, #ddd); }
.metric-name { font-size: 14px; font-weight: 700; margin-bottom: 8px; }
.metric-values { display: grid; gap: 6px; }
.metric-value-line { display: flex; justify-content: space-between; font-size: 12px; }
.charts-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 12px; margin: 12px 24px; }
</style>