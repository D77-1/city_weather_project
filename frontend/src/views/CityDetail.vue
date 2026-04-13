<template>
  <div class="city-detail page-shell">
    <AppHeader @city-change="onCityChange" />

    <div v-loading="loading">
      <section class="page-section detail-hero" v-if="displayData.aqi != null">
        <div class="section-heading">
          <span class="section-kicker">CITY REPORT</span>
          <h2 class="section-title">城市空气质量解读</h2>
        </div>

        <div class="detail-hero-grid">
          <el-card class="detail-hero-main">
            <div class="hero-main-top">
              <div>
                <p class="detail-city-name">{{ city?.name }}</p>
                <h3 class="detail-report-title">城市空气质量研究摘要</h3>
              </div>
              <span class="report-chip">RESEARCH NOTE</span>
            </div>

            <div class="detail-aqi-row">
              <span class="detail-aqi-value" :style="{ color: aqiColor(displayData.aqi) }">{{ displayData.aqi }}</span>
              <div class="detail-aqi-meta">
                <strong>{{ displayData.qualityLevel }}</strong>
                <span>数据来源：{{ displayData.source }}</span>
                <span>更新时间：{{ displayData.updateTime || '--' }}</span>
              </div>
            </div>

            <div class="hero-main-divider" />

            <div class="hero-main-footnote">
              <span class="mini-kicker">页内说明</span>
              <p>本页以城市为单位整合趋势预测、异常检测、风险评估与原始数据对照，适合在答辩中作为单城研究样例进行讲解。</p>
            </div>
          </el-card>

          <el-card class="detail-risk-card">
            <p class="mini-title">综合风险</p>
            <div class="risk-score-large" :style="{ color: riskColor(aqStore.riskResult?.level) }">{{ aqStore.riskResult?.score ?? '--' }}</div>
            <el-tag :type="riskTagType(aqStore.riskResult?.level)">{{ riskLevelText(aqStore.riskResult?.level) }}</el-tag>
            <div class="risk-side-copy">
              <span class="mini-kicker">结论摘要</span>
              <p>{{ aqStore.riskResult?.summary || '暂无结果' }}</p>
            </div>
          </el-card>
        </div>
      </section>

      <section class="page-section pollutant-section" v-if="pollutantCards.length">
        <div class="detail-pollutant-grid">
          <el-card v-for="item in pollutantCards" :key="item.label" class="pollutant-card">
            <span>{{ item.label }}</span>
            <b>{{ item.value ?? '--' }}</b>
            <small>{{ item.unit }}</small>
          </el-card>
        </div>
      </section>

      <section class="page-section detail-analysis-grid">
        <div>
          <div class="section-heading">
            <span class="section-kicker">ANALYSIS</span>
            <h2 class="section-title">核心分析</h2>
          </div>

          <el-card class="detail-trend-card">
            <template #header>
              <div class="card-header trend-header">
                <div>
                  <span>{{ metricLabel }} 走势与预测</span>
                  <p>展示历史变化、参考线与预测结果。</p>
                </div>
                <div class="analysis-controls">
                  <el-select v-model="selectedMetric" size="small" style="width: 110px" @change="loadFullData">
                    <el-option label="AQI" value="aqi" />
                    <el-option label="PM2.5" value="pm25" />
                    <el-option label="PM10" value="pm10" />
                    <el-option label="O3" value="o3" />
                  </el-select>
                  <el-select v-model="selectedAlgorithm" size="small" style="width: 150px" @change="loadFullData">
                    <el-option v-for="item in algorithmOptions" :key="item.value" :label="item.label" :value="item.value" />
                  </el-select>
                  <el-select v-model="selectedAnomalyMethod" size="small" style="width: 120px" @change="loadFullData">
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
            <TrendLine
              :trend-data="combinedTrend"
              :title="`${city?.name || ''} ${metricLabel} 走势`"
              :metric="metricLabel"
              :algorithm-label="`${algorithmLabel}预测`"
              :reference-label="referenceLabel"
              height="400px"
            />
          </el-card>
        </div>

        <div class="detail-analysis-side">
          <el-card class="analysis-side-card">
            <template #header>
              <div class="card-header card-header--stacked">
                <div>
                  <span>未来 5 天多指标预测摘要</span>
                  <p>对各项关键污染指标进行短期预测。</p>
                </div>
              </div>
            </template>
            <div class="metric-summary-grid">
              <div v-for="metric in metricCards" :key="metric.key" class="metric-summary-item">
                <strong>{{ metric.label }}</strong>
                <div v-for="row in metric.items" :key="row.date" class="metric-summary-row">
                  <span>{{ row.date?.slice(5) }}</span>
                  <b>{{ row.predicted }}</b>
                </div>
              </div>
            </div>
          </el-card>

          <el-card class="analysis-side-card">
            <template #header>
              <div class="card-header card-header--stacked">
                <div>
                  <span>{{ anomalyMethodLabel }} 异常检测</span>
                  <p>对历史序列中的异常波动进行对比说明。</p>
                </div>
              </div>
            </template>
            <div class="analysis-note-grid">
              <div class="analysis-note-item">
                <span>数据点</span>
                <b>{{ aqStore.anomalyResult?.total_points ?? 0 }}</b>
              </div>
              <div class="analysis-note-item">
                <span>异常数</span>
                <b>{{ aqStore.anomalyResult?.anomaly_count ?? 0 }}</b>
              </div>
            </div>
            <div class="list-stack">
              <div v-for="item in aqStore.anomalyResult?.comparison || []" :key="item.method" class="driver-row">
                <span>{{ anomalyMethodText(item.method) }}</span>
                <b>{{ item.anomalyCount }}</b>
              </div>
            </div>
          </el-card>
        </div>
      </section>

      <section class="page-section" v-if="comparisonRows.length">
        <div class="section-heading compact-heading">
          <span class="section-kicker">EVALUATION</span>
          <h2 class="section-title">模型准确性对比评估</h2>
        </div>
        <el-card class="eval-card">
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>{{ metricLabel }} 预测算法精度对比</span>
                <p>基于历史回测，对 6 种预测模型的误差指标进行横向对比，MAPE 越低越优。</p>
              </div>
            </div>
          </template>
          <el-table :data="comparisonRows" stripe size="small" :default-sort="{ prop: 'mape', order: 'ascending' }">
            <el-table-column prop="label" label="算法" width="160">
              <template #default="{ row }">
                <div class="algo-cell">
                  <span>{{ row.label }}</span>
                  <el-tag v-if="row.isBest" type="success" size="small" effect="dark">推荐</el-tag>
                  <el-tag v-if="!row.available" type="info" size="small">不可用</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="mae" label="MAE" width="100" sortable :formatter="(r,c,v) => v ?? '--'" />
            <el-table-column prop="rmse" label="RMSE" width="100" sortable :formatter="(r,c,v) => v ?? '--'" />
            <el-table-column prop="mape" label="MAPE(%)" width="110" sortable>
              <template #default="{ row }">
                <span :class="{ 'best-val': row.isBest }">{{ row.mape != null ? row.mape + '%' : '--' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="r2" label="R²" width="100" sortable :formatter="(r,c,v) => v ?? '--'" />
            <el-table-column prop="statusText" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.available ? 'success' : 'warning'" size="small">{{ row.statusText }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
          <div class="eval-note">
            <p>MAE: 平均绝对误差 | RMSE: 均方根误差 | MAPE: 平均绝对百分比误差 | R²: 拟合优度（越接近 1 越好）</p>
          </div>
        </el-card>
      </section>

      <section class="page-section detail-explain-grid">
        <div class="section-heading">
          <span class="section-kicker">INTERPRETATION</span>
          <h2 class="section-title">风险与健康建议</h2>
        </div>
        <el-card class="risk-card">
          <div class="analysis-note">{{ aqStore.riskResult?.summary }}</div>
          <div class="list-stack">
            <div class="driver-row"><span>污染暴露</span><b>{{ aqStore.riskResult?.components?.pollution ?? '--' }}</b></div>
            <div class="driver-row"><span>扩散条件</span><b>{{ aqStore.riskResult?.components?.diffusion ?? '--' }}</b></div>
            <div class="driver-row"><span>异常波动</span><b>{{ aqStore.riskResult?.components?.anomaly ?? '--' }}</b></div>
            <div class="driver-row"><span>未来趋势</span><b>{{ aqStore.riskResult?.components?.forecast ?? '--' }}</b></div>
          </div>
        </el-card>
        <HealthAdvice
          v-if="displayData.aqi != null"
          :aqi="displayData.aqi"
          :quality-level="displayData.qualityLevel"
          :risk-level="aqStore.riskResult?.level"
          :future-summary="aqStore.riskResult?.summary"
          :main-pollutants="(aqStore.riskResult?.drivers || []).slice(0, 3).map(d => d.factor)"
        />
      </section>

      <section class="page-section detail-data-grid">
        <div class="section-heading">
          <span class="section-kicker">DETAILS</span>
          <h2 class="section-title">数据明细</h2>
        </div>

        <el-card>
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>数据库值 vs 实时值</span>
                <p>说明数据库聚合结果与实时接口之间的差异。</p>
              </div>
            </div>
          </template>
          <el-table :data="realtimeCompareRows" stripe size="small">
            <el-table-column prop="name" label="指标" />
            <el-table-column prop="dbValue" label="数据库最新值" />
            <el-table-column prop="realValue" label="实时值" />
            <el-table-column prop="diff" label="差值" />
          </el-table>
        </el-card>

        <el-card>
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>达标了吗？</span>
                <p>根据国标限值判断主要污染物是否超标。</p>
              </div>
            </div>
          </template>
          <el-table :data="pollutantTable" stripe size="small">
            <el-table-column prop="name" label="污染物" width="90" />
            <el-table-column prop="value" label="当前值" width="90" />
            <el-table-column prop="limit" label="国标限值" width="90" />
            <el-table-column label="达标">
              <template #default="{ row }">
                <el-tag :type="row.value <= row.limit ? 'success' : 'danger'" size="small">{{ row.value <= row.limit ? '达标' : '超标' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-card>
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>近 {{ days }} 天统计</span>
                <p>展示指定时间窗内的均值、峰值与基础城市信息。</p>
              </div>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="8" v-for="item in historyStats" :key="item.label">
              <el-statistic :title="item.label" :value="item.value" />
            </el-col>
          </el-row>
          <el-descriptions :column="3" border style="margin-top: 16px">
            <el-descriptions-item label="省份">{{ city?.province }}</el-descriptions-item>
            <el-descriptions-item label="城市编码">{{ city?.cityCode }}</el-descriptions-item>
            <el-descriptions-item label="监测站点">{{ stations.map((item) => item.stationName).join('、') || '--' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </section>
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
// 实时数据优先，fallback 到数据库值
const displayData = computed(() => {
  const rt = aqStore.realtimeLatest
  const db = latestCity.value
  if (rt?.aqi != null) {
    return {
      aqi: rt.aqi,
      qualityLevel: rt.qualityLevel || db?.qualityLevel,
      pm25: rt.pm25 ?? db?.pm25,
      pm10: rt.pm10 ?? db?.pm10,
      so2: rt.so2 ?? db?.so2,
      no2: rt.no2 ?? db?.no2,
      co: rt.co ?? db?.co,
      o3: rt.o3 ?? db?.o3,
      source: 'Open-Meteo 实时',
      updateTime: rt.updateTime || '',
    }
  }
  if (!db) return {}
  return { ...db, source: db.dataSource || 'local_db_daily_avg', updateTime: db.recordDate || '' }
})
const combinedTrend = computed(() => aqStore.trendWithPrediction)
const referenceLabel = computed(() => aqStore.predictionMeta?.referenceLabel || '参考线')

// 算法精度对比表数据
const comparisonRows = computed(() => {
  const comp = aqStore.predictionResult?.comparison || []
  if (!comp.length) return []

  const algoLabels = {
    moving_average: '移动平均 (MA)',
    weighted_moving_average: '加权移动平均 (WMA)',
    linear_regression: '线性回归 (LR)',
    holt_winters: 'Holt-Winters 指数平滑',
    arima: 'ARIMA 时序模型',
    lstm: 'LSTM 深度学习',
  }

  // 找 MAPE 最低的作为推荐
  const validComps = comp.filter(c => c.mape != null && c.available !== false)
  const bestMape = validComps.length ? Math.min(...validComps.map(c => c.mape)) : null

  return comp.map(c => ({
    algorithm: c.algorithm,
    label: algoLabels[c.algorithm] || c.algorithm,
    mae: c.mae,
    rmse: c.rmse,
    mape: c.mape,
    r2: c.r2,
    available: c.available !== false,
    statusText: c.available !== false ? '可用' : '回退',
    isBest: c.mape === bestMape && c.available !== false,
  }))
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
const pollutantCards = computed(() => {
  const c = displayData.value
  if (!c || c.aqi == null) return []
  return [
    { label: 'PM2.5', value: c.pm25, unit: 'μg/m³' },
    { label: 'PM10', value: c.pm10, unit: 'μg/m³' },
    { label: 'SO₂', value: c.so2, unit: 'μg/m³' },
    { label: 'NO₂', value: c.no2, unit: 'μg/m³' },
    { label: 'CO', value: c.co, unit: 'mg/m³' },
    { label: 'O₃', value: c.o3, unit: 'μg/m³' },
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
  const c = displayData.value
  if (!c || c.aqi == null) return []
  return [
    { name: 'PM2.5', value: c.pm25, unit: 'μg/m³', limit: 75 },
    { name: 'PM10', value: c.pm10, unit: 'μg/m³', limit: 150 },
    { name: 'SO₂', value: c.so2, unit: 'μg/m³', limit: 60 },
    { name: 'NO₂', value: c.no2, unit: 'μg/m³', limit: 80 },
    { name: 'CO', value: c.co, unit: 'mg/m³', limit: 4 },
    { name: 'O₃', value: c.o3, unit: 'μg/m³', limit: 160 },
  ]
})
const historyStats = computed(() => {
  const h = aqStore.historyRecords
  if (!h?.length) return []
  const key = { aqi: 'aqi', pm25: 'pm25', pm10: 'pm10', o3: 'o3' }[selectedMetric.value]
  const values = h.map((item) => item[key]).filter((item) => item != null)
  if (!values.length) return []
  const avg = (values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(1)
  return [
    { label: `${metricLabel.value}均值`, value: avg },
    { label: `${metricLabel.value}最高`, value: Math.max(...values) },
    { label: `${metricLabel.value}最低`, value: Math.min(...values) },
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

function onCityChange(cityId) {
  router.push(`/city/${cityId}`)
}
function onDaysChange() {
  const id = Number(route.params.id)
  if (id) aqStore.fetchHistory(id, days.value)
}
function algorithmText(value) {
  return ({ moving_average: '移动平均', weighted_moving_average: '加权移动平均', linear_regression: '线性回归', holt_winters: 'Holt-Winters', arima: 'ARIMA', lstm: 'LSTM' }[value] || value)
}
function anomalyMethodText(value) {
  return ({ iqr: 'IQR', zscore: 'Z-score', mad: 'MAD' }[value] || value)
}
function riskTagType(level) {
  return ({ low: 'success', medium: 'warning', high: 'danger', severe: 'danger' }[level] || 'info')
}
function riskLevelText(level) {
  return ({ low: '低风险', medium: '中风险', high: '高风险', severe: '极高风险' }[level] || level)
}
function riskColor(level) {
  return ({ low: '#0b8f6a', medium: '#b7791f', high: '#b42318', severe: '#7a1f1a' }[level] || '#1f2937')
}
function diffText(dbValue, realValue) {
  if (dbValue == null || realValue == null) return '--'
  return (Number(dbValue) - Number(realValue)).toFixed(1)
}
function aqiColor(aqi) {
  if (!aqi) return '#8a8a8a'
  if (aqi <= 50) return '#2d6a4f'
  if (aqi <= 100) return '#d4a373'
  if (aqi <= 150) return '#e07a5f'
  if (aqi <= 200) return '#c1121f'
  return '#780116'
}

watch(() => route.params.id, loadFullData)

onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  loadFullData()
})
</script>

<style scoped>
.city-detail {
  padding-bottom: 28px;
}

.detail-hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(290px, 0.78fr);
  gap: 16px;
}

.detail-hero-main,
.detail-risk-card,
.analysis-side-card,
.risk-card {
  background: rgba(255, 252, 247, 0.78) !important;
}

.detail-hero-main,
.detail-risk-card {
  padding: 26px;
}

.hero-main-top,
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-header--stacked p,
.card-header p,
.hero-main-footnote p,
.risk-side-copy p {
  margin-top: 4px;
}

.detail-city-name,
.mini-title,
.mini-kicker {
  font-family: var(--aq-mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.detail-city-name,
.mini-title {
  color: var(--aq-muted);
}

.detail-report-title {
  margin-top: 10px;
  font-family: var(--aq-display);
  font-size: 34px;
  line-height: 1.1;
  color: var(--aq-ink);
}

.report-chip {
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--aq-line-strong);
  color: var(--aq-accent);
  font-family: var(--aq-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.detail-aqi-row {
  display: flex;
  gap: 18px;
  align-items: flex-end;
  margin-top: 22px;
}

.detail-aqi-value {
  font-size: 88px;
  line-height: 0.95;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.detail-aqi-meta {
  display: grid;
  gap: 8px;
  padding-bottom: 10px;
  color: var(--aq-ink-soft);
}

.detail-aqi-meta strong,
.metric-summary-item strong {
  color: var(--aq-ink);
}

.hero-main-divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(168, 116, 63, 0.35), rgba(168, 116, 63, 0));
  margin: 18px 0 14px;
}

.hero-main-footnote {
  display: grid;
  gap: 8px;
}

.mini-kicker {
  color: var(--aq-accent);
}

.hero-main-footnote p,
.risk-side-copy p,
.analysis-note,
.analysis-note-item span,
.card-header p {
  color: var(--aq-ink-soft);
}

.risk-score-large {
  font-size: 62px;
  font-weight: 800;
  margin: 10px 0 12px;
}

.risk-side-copy {
  display: grid;
  gap: 8px;
  margin-top: 18px;
}

.detail-pollutant-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.pollutant-card {
  display: grid;
  gap: 8px;
  background: rgba(255, 252, 247, 0.72) !important;
}

.pollutant-card span,
.pollutant-card small {
  color: var(--aq-ink-soft);
}

.pollutant-card b {
  font-family: var(--aq-display);
  font-size: 30px;
  color: var(--aq-ink);
}

.detail-analysis-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(320px, 0.95fr);
  gap: 18px;
}

.detail-analysis-side,
.metric-summary-grid,
.detail-data-grid,
.detail-explain-grid,
.list-stack,
.analysis-note-grid {
  display: grid;
  gap: 14px;
}

.analysis-controls {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.trend-header {
  align-items: center;
}

.detail-trend-card {
  background: rgba(255, 252, 247, 0.78) !important;
}

.driver-row,
.metric-summary-item,
.analysis-note-item {
  border-radius: 14px;
  border: 1px solid rgba(30, 92, 90, 0.08);
  background: linear-gradient(180deg, rgba(30, 92, 90, 0.07), rgba(168, 116, 63, 0.05));
}

.driver-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
}

.metric-summary-item,
.analysis-note-item {
  padding: 12px 14px;
}

.metric-summary-item {
  display: grid;
  gap: 10px;
}

.metric-summary-row {
  display: flex;
  justify-content: space-between;
  color: var(--aq-ink-soft);
}

.metric-summary-row b,
.driver-row b,
.analysis-note-item b {
  color: var(--aq-ink);
}

.analysis-note-item {
  display: grid;
  gap: 4px;
}

.risk-card {
  padding: 18px;
}

.eval-card {
  background: rgba(255, 252, 247, 0.78) !important;
}

.algo-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.best-val {
  color: #2d6a4f;
  font-weight: 700;
}

.eval-note {
  margin-top: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(30, 92, 90, 0.05);
}

.eval-note p {
  font-size: 12px;
  color: var(--aq-ink-soft);
}

@media (max-width: 1280px) {
  .detail-hero-grid,
  .detail-analysis-grid,
  .detail-pollutant-grid,
  .detail-explain-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .detail-aqi-row,
  .trend-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
