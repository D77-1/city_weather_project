<template>
  <div class="dashboard page-shell">
    <AppHeader @city-change="onCityChange" />

    <section class="page-section hero-section">
      <div class="section-heading">
        <span class="section-kicker">CITY OVERVIEW</span>
        <h2 class="section-title">城市空气态势总览</h2>
      </div>

      <div class="hero-band">
        <el-card class="hero-main-card">
          <div class="hero-card-top">
            <div>
              <p class="hero-label">当前展示城市</p>
              <div class="hero-city-line">
                <strong>{{ selectedCityName }}</strong>
                <el-tag :type="aqiTagType(currentCityLatest.aqi || 0)" size="small">{{ currentCityLatest.qualityLevel ?? '--' }}</el-tag>
              </div>
            </div>
            <span class="hero-panel-tag">DEFENSE PANEL</span>
          </div>

          <div class="hero-aqi-block">
            <div class="hero-aqi-value" :style="{ color: aqiColor(currentCityLatest.aqi) }">{{ currentCityLatest.aqi ?? '--' }}</div>
            <div class="hero-aqi-copy">
              <p>空气质量指数 AQI</p>
              <span>数据库日期：{{ currentCityLatest.recordDate || '--' }}</span>
              <span>数据来源：{{ currentCityLatest.dataSource || 'local_db_daily_avg' }}</span>
            </div>
          </div>

          <div class="hero-divider" />

          <div class="hero-footnote">
            <span class="footnote-label">展示说明</span>
            <p>本页优先展示城市当前状态、全国空间分布与未来风险变化，适合答辩时快速说明系统的数据接入、可视化与分析链路。</p>
          </div>
        </el-card>

        <div class="hero-side-grid">
          <el-card v-for="item in overviewCards" :key="item.label" class="hero-metric-card">
            <span class="metric-kicker">{{ item.label }}</span>
            <b>{{ item.value }}</b>
            <small>核心观测指标</small>
          </el-card>
        </div>
      </div>
    </section>

    <section class="page-section dashboard-grid">
      <div class="map-column">
        <div class="section-heading compact-heading">
          <span class="section-kicker">VISUALIZATION</span>
          <h2 class="section-title">全国空气态势</h2>
        </div>
        <el-card class="map-panel map-card">
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>全国城市空气质量地图</span>
                <p>从空间分布层面展示重点城市 AQI 水平与区域差异。</p>
              </div>
            </div>
          </template>
          <ChinaMap :data="aqStore.mapData" height="520px" @city-click="onMapCityClick" />
        </el-card>
      </div>

      <div class="side-column">
        <div class="section-heading compact-heading">
          <span class="section-kicker">RANKING</span>
          <h2 class="section-title">重点城市观察</h2>
        </div>

        <el-card class="side-panel">
          <template #header>
            <div class="card-header">
              <div>
                <span>城市空气质量排名</span>
                <p>点击城市可进入详细分析页。</p>
              </div>
              <el-button text size="small" @click="toggleRankOrder">{{ rankOrder === 'desc' ? '最优排序' : '最差排序' }}</el-button>
            </div>
          </template>
          <div class="list-stack">
            <div v-for="item in aqStore.rankingList" :key="item.cityId" class="rank-row" @click="onRankCityClick(item.cityId)">
              <span class="rank-num">{{ item.rank }}</span>
              <span class="rank-name">{{ item.cityName }}</span>
              <el-tag :type="aqiTagType(item.aqi)" size="small">{{ item.aqi }} {{ item.qualityLevel }}</el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="side-panel">
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>未来 5 天风险</span>
                <p>结合预测与风险评估结果生成答辩展示摘要。</p>
              </div>
            </div>
          </template>
          <div class="list-stack">
            <div v-if="!futureRiskList.length" class="empty-tip">暂无风险数据</div>
            <div v-for="item in futureRiskList" :key="item.date" class="risk-row">
              <el-tag :type="riskTagType(item.level)" size="small">{{ riskLevelText(item.level) }}</el-tag>
              <span>{{ item.date }}</span>
              <b>{{ item.score }}</b>
            </div>
          </div>
        </el-card>
      </div>
    </section>

    <section class="page-section analysis-section">
      <div class="section-heading">
        <span class="section-kicker">ANALYSIS</span>
        <h2 class="section-title">分析能力概览</h2>
      </div>

      <div class="analysis-cards">
        <el-card class="analysis-card">
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>预测摘要</span>
                <p>当前算法与历史区间用于说明趋势预测能力。</p>
              </div>
            </div>
          </template>
          <div class="analysis-note-grid">
            <div class="analysis-note-item">
              <span>当前算法</span>
              <b>{{ algorithmText(aqStore.predictionMeta?.selectedAlgorithm || selectedAlgorithm) }}</b>
            </div>
            <div class="analysis-note-item">
              <span>历史区间</span>
              <b>{{ predictionRangeText }}</b>
            </div>
            <div class="analysis-note-item">
              <span>未来摘要</span>
              <p>{{ aqStore.riskResult?.summary || '暂无结果' }}</p>
            </div>
          </div>
        </el-card>

        <el-card class="analysis-card">
          <template #header>
            <div class="card-header card-header--stacked">
              <div>
                <span>风险驱动因素</span>
                <p>展示模型判断中贡献度较高的关键因子。</p>
              </div>
            </div>
          </template>
          <div class="list-stack">
            <div v-for="item in topDrivers" :key="item.factor" class="driver-row">
              <span>{{ item.label || item.factor }}</span>
              <b>{{ item.contribution }}</b>
            </div>
          </div>
        </el-card>

        <el-card class="analysis-card">
          <template #header>
            <div class="card-header">
              <div>
                <span>算法状态</span>
                <p>用于展示不同预测算法的当前可用情况。</p>
              </div>
              <el-select v-model="selectedAlgorithm" size="small" style="width: 150px" @change="reloadPrediction">
                <el-option v-for="item in algorithmOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>
          </template>
          <div class="list-stack">
            <div v-for="item in availabilityList" :key="item.key" class="driver-row">
              <span>{{ item.label }}</span>
              <el-tag :type="item.available ? 'success' : 'warning'" size="small">{{ item.available ? '可用' : '回退' }}</el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </section>

    <section class="page-section support-section">
      <div class="section-heading">
        <span class="section-kicker">SUPPORT</span>
        <h2 class="section-title">辅助说明</h2>
      </div>

      <HealthAdvice
        v-if="currentCityLatest.aqi"
        :aqi="currentCityLatest.aqi"
        :quality-level="currentCityLatest.qualityLevel"
        :risk-level="aqStore.riskResult?.level"
        :future-summary="aqStore.riskResult?.summary"
        :main-pollutants="(aqStore.riskResult?.drivers || []).slice(0, 3).map(d => d.factor)"
      />

      <el-card v-if="realtimeCompareRows.length" class="support-card">
        <template #header>
          <div class="card-header">
            <div>
              <span>数据库值 vs 实时值</span>
              <p>用于说明系统本地数据库与 Open-Meteo 接口之间的对照关系。</p>
            </div>
            <el-tag size="small" effect="plain">Open-Meteo 对照</el-tag>
          </div>
        </template>
        <div class="realtime-topbar" v-if="aqStore.realtimeLatest?.source">
          <div class="realtime-main">
            <div class="realtime-city">{{ selectedCityName }} 实时空气质量</div>
            <div class="realtime-source">{{ aqStore.realtimeLatest.source }}</div>
          </div>
          <div class="realtime-weather" v-if="aqStore.realtimeLatest.weather">
            <span>{{ aqStore.realtimeLatest.weather.weatherEmoji || '' }} {{ aqStore.realtimeLatest.weather.weatherText || '天气' }}</span>
            <b>{{ aqStore.realtimeLatest.weather.temperature ?? '--' }}℃</b>
          </div>
        </div>
        <el-table :data="realtimeCompareRows" stripe size="small">
          <el-table-column prop="name" label="指标" />
          <el-table-column prop="dbValue" label="数据库最新值" />
          <el-table-column prop="realValue" label="实时值" />
          <el-table-column prop="diff" label="差值" />
        </el-table>
        <div class="realtime-pill-row" v-if="realtimePills.length">
          <div v-for="item in realtimePills" :key="item.label" class="realtime-pill">
            <span>{{ item.label }}</span>
            <b>{{ item.value }}</b>
          </div>
        </div>
      </el-card>

      <AiChatWindow :city-id="cityStore.currentCityId" :city-name="selectedCityName" :context="aiContext" />
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCityStore } from '@/stores/city'
import { useAirQualityStore } from '@/stores/airQuality'
import AppHeader from '@/components/layout/AppHeader.vue'
import ChinaMap from '@/components/charts/ChinaMap.vue'
import AiChatWindow from '@/components/ai/AiChatWindow.vue'
import HealthAdvice from '@/components/HealthAdvice.vue'

const router = useRouter()
const cityStore = useCityStore()
const aqStore = useAirQualityStore()
const rankOrder = ref('desc')
const selectedAlgorithm = ref('holt_winters')
const algorithmOptions = [
  { label: '移动平均', value: 'moving_average' },
  { label: '加权移动平均', value: 'weighted_moving_average' },
  { label: '线性回归', value: 'linear_regression' },
  { label: 'Holt-Winters', value: 'holt_winters' },
  { label: 'ARIMA', value: 'arima' },
  { label: 'LSTM', value: 'lstm' },
]

const selectedCityName = computed(() => cityStore.currentCity?.name || '全国')
const currentCityLatest = computed(() => aqStore.latestData.find((d) => d.cityId === cityStore.currentCityId) || {})
const predictionRangeText = computed(() => {
  const meta = aqStore.predictionMeta
  if (!meta?.historyStart || !meta?.historyEnd) return '--'
  return `${meta.historyStart} ~ ${meta.historyEnd}`
})
const overviewCards = computed(() => [
  { label: '综合风险', value: aqStore.riskResult?.score ?? '--' },
  { label: 'PM2.5', value: currentCityLatest.value.pm25 ?? '--' },
  { label: 'PM10', value: currentCityLatest.value.pm10 ?? '--' },
  { label: '实时天气', value: aqStore.realtimeLatest?.weather?.weatherText || '--' },
])
const topDrivers = computed(() => (aqStore.riskResult?.drivers || []).slice(0, 4))
const futureRiskList = computed(() => (aqStore.riskResult?.futureRisk || []).slice(0, 5))
const availabilityList = computed(() => Object.entries(aqStore.predictionMeta?.availability || {}).map(([key, value]) => ({
  key,
  label: algorithmText(key),
  available: value.available,
})))
const realtimeCompareRows = computed(() => {
  const dbRow = currentCityLatest.value
  const rt = aqStore.realtimeLatest
  if (!dbRow || !rt?.source) return []
  return [
    { name: 'AQI', dbValue: dbRow.aqi ?? '--', realValue: rt.aqi ?? '--', diff: diffText(dbRow.aqi, rt.aqi) },
    { name: 'PM2.5', dbValue: dbRow.pm25 ?? '--', realValue: rt.pm25 ?? '--', diff: diffText(dbRow.pm25, rt.pm25) },
    { name: 'PM10', dbValue: dbRow.pm10 ?? '--', realValue: rt.pm10 ?? '--', diff: diffText(dbRow.pm10, rt.pm10) },
    { name: 'O₃', dbValue: dbRow.o3 ?? '--', realValue: rt.o3 ?? '--', diff: diffText(dbRow.o3, rt.o3) },
  ]
})
const realtimePills = computed(() => {
  const rt = aqStore.realtimeLatest
  if (!rt?.source) return []
  return [
    { label: 'AQI', value: rt.aqi ?? '--' },
    { label: 'PM2.5', value: rt.pm25 ?? '--' },
    { label: 'PM10', value: rt.pm10 ?? '--' },
    { label: 'O₃', value: rt.o3 ?? '--' },
    { label: '降水', value: rt.weather?.rainfall != null ? `${rt.weather.rainfall} mm` : '--' },
  ]
})
const aiContext = computed(() => ({
  cityName: selectedCityName.value,
  current: currentCityLatest.value,
  prediction: aqStore.predictionResult?.predictions?.slice(0, 5),
  selectedAlgorithm: aqStore.predictionResult?.selectedAlgorithm,
  comparison: aqStore.predictionResult?.comparison || [],
  risk: aqStore.riskResult,
  multiMetricPrediction: aqStore.riskResult?.metricPredictions || {},
  anomalies: aqStore.anomalyList.slice(0, 3).map((a) => ({
    date: a.recordTime?.slice(0, 10),
    metric: a.metricName,
    value: a.actualValue,
    severity: a.severity,
    type: a.anomalyType,
  })),
}))

async function loadCityData(cityId) {
  if (!cityId) return
  await Promise.all([
    aqStore.fetchPrediction(cityId, 'aqi', 7, 5, selectedAlgorithm.value, true),
    aqStore.fetchRealtimeLatest(cityId),
    aqStore.fetchAnomalyList({ city_id: cityId, limit: 10 }),
    aqStore.fetchRiskAssess(cityId, 5),
  ])
}

function reloadPrediction() {
  if (cityStore.currentCityId) loadCityData(cityStore.currentCityId)
}
function onCityChange(cityId) {
  cityStore.selectCity(cityId)
}
function onMapCityClick({ cityId }) {
  cityStore.selectCity(cityId)
}
function onRankCityClick(cityId) {
  router.push(`/city/${cityId}`)
}
function toggleRankOrder() {
  rankOrder.value = rankOrder.value === 'desc' ? 'asc' : 'desc'
  aqStore.fetchRanking(rankOrder.value, 10)
}
function algorithmText(value) {
  return ({ moving_average: '移动平均', weighted_moving_average: '加权移动平均', linear_regression: '线性回归', holt_winters: 'Holt-Winters', arima: 'ARIMA', lstm: 'LSTM' }[value] || value)
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
function aqiTagType(aqi) {
  if (aqi <= 50) return 'success'
  if (aqi <= 100) return 'warning'
  if (aqi <= 200) return 'danger'
  return 'danger'
}
function riskLevelText(level) {
  return ({ low: '低风险', medium: '中风险', high: '高风险', severe: '极高风险' }[level] || level)
}
function riskTagType(level) {
  return ({ low: 'success', medium: 'warning', high: 'danger', severe: 'danger' }[level] || 'info')
}

watch(() => cityStore.currentCityId, (newId) => {
  if (newId) loadCityData(newId)
})

onMounted(async () => {
  await cityStore.fetchCities()
  await Promise.all([aqStore.fetchLatest(), aqStore.fetchMapData(), aqStore.fetchRanking('desc', 10)])
  if (cityStore.cities.length > 0 && !cityStore.currentCityId) cityStore.selectCity(cityStore.cities[0].id)
  if (cityStore.currentCityId) loadCityData(cityStore.currentCityId)
})
</script>

<style scoped>
.dashboard {
  padding-bottom: 28px;
}

.hero-band {
  display: grid;
  grid-template-columns: minmax(320px, 1.2fr) minmax(0, 1fr);
  gap: 18px;
}

.hero-main-card {
  padding: 28px;
  background:
    linear-gradient(135deg, rgba(255, 252, 247, 0.82), rgba(251, 247, 239, 0.72)),
    radial-gradient(circle at top right, rgba(168, 116, 63, 0.08), transparent 36%) !important;
}

.hero-card-top,
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-header--stacked p,
.card-header p,
.hero-footnote p,
.analysis-note-item p {
  margin-top: 4px;
}

.hero-label,
.metric-kicker,
.footnote-label {
  font-family: var(--aq-mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.hero-label,
.metric-kicker {
  color: var(--aq-muted);
}

.hero-panel-tag {
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--aq-line-strong);
  color: var(--aq-accent);
  font-family: var(--aq-mono);
  font-size: 11px;
  letter-spacing: 0.12em;
}

.hero-city-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.hero-city-line strong {
  font-family: var(--aq-display);
  font-size: 34px;
  font-weight: 700;
  color: var(--aq-ink);
}

.hero-aqi-block {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 20px;
  align-items: end;
  margin: 22px 0 16px;
}

.hero-aqi-value {
  font-size: 92px;
  line-height: 0.95;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.hero-aqi-copy {
  display: grid;
  gap: 8px;
  padding-bottom: 10px;
}

.hero-aqi-copy p,
.analysis-note-item b,
.realtime-city {
  font-weight: 700;
  color: var(--aq-ink);
}

.hero-aqi-copy span,
.hero-footnote p,
.card-header p,
.analysis-note-item span,
.analysis-note-item p,
.realtime-source,
.empty-tip {
  color: var(--aq-ink-soft);
}

.hero-divider {
  height: 1px;
  background: linear-gradient(90deg, rgba(168, 116, 63, 0.35), rgba(168, 116, 63, 0));
  margin: 16px 0 14px;
}

.hero-footnote {
  display: grid;
  gap: 8px;
}

.footnote-label {
  color: var(--aq-accent);
}

.hero-side-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.hero-metric-card,
.analysis-card,
.side-panel,
.support-card {
  background: rgba(255, 252, 247, 0.76) !important;
}

.hero-metric-card {
  display: grid;
  gap: 12px;
  align-content: end;
  min-height: 148px;
}

.hero-metric-card b {
  font-family: var(--aq-display);
  font-size: 34px;
  color: var(--aq-ink);
}

.hero-metric-card small {
  color: var(--aq-ink-soft);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.92fr);
  gap: 18px;
}


.side-column,
.list-stack,
.support-section {
  display: grid;
  gap: 14px;
}

.map-column{
  gap: 14px;
}

.map-panel {
  min-height: 560px;
}

.map-card {
  background:
    linear-gradient(180deg, rgba(19, 28, 33, 0.96), rgba(14, 21, 25, 0.98)),
    radial-gradient(circle at top, rgba(126, 181, 175, 0.14), transparent 38%) !important;
  overflow: hidden;
}

.map-card :deep(.el-card__header) {
  border-bottom-color: rgba(255, 255, 255, 0.1) !important;
  color: #eff4f2 !important;
}

.map-card :deep(.el-card__header p) {
  color: rgba(239, 244, 242, 0.68) !important;
}

.rank-row,
.risk-row,
.driver-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(30, 92, 90, 0.08);
  background: linear-gradient(180deg, rgba(30, 92, 90, 0.07), rgba(168, 116, 63, 0.05));
}

.rank-row {
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease;
}

.rank-row:hover {
  transform: translateY(-1px);
  border-color: rgba(168, 116, 63, 0.22);
}

.rank-num {
  width: 28px;
  text-align: center;
  font-family: var(--aq-mono);
  font-weight: 700;
  color: var(--aq-accent);
}

.rank-name,
.risk-row span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.analysis-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.analysis-note-grid {
  display: grid;
  gap: 12px;
}

.analysis-note-item {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.46);
  border: 1px solid rgba(26, 37, 41, 0.06);
}

.realtime-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.realtime-main {
  display: grid;
  gap: 2px;
}

.realtime-weather {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--aq-ink-soft);
}

.realtime-pill-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 8px;
  margin-top: 12px;
}

.realtime-pill {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 9px 11px;
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(30, 92, 90, 0.08), rgba(168, 116, 63, 0.05));
  font-size: 12px;
}

.realtime-pill span {
  color: var(--aq-ink-soft);
}

.realtime-pill b {
  color: var(--aq-primary);
}

@media (max-width: 1280px) {
  .hero-band,
  .dashboard-grid,
  .analysis-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .hero-side-grid {
    grid-template-columns: 1fr;
  }

  .hero-aqi-block {
    grid-template-columns: 1fr;
    align-items: start;
  }
}
</style>
