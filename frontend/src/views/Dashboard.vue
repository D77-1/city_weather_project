<template>
  <div class="dashboard">
    <AppHeader @city-change="onCityChange" />

    <div class="kpi-row">
      <el-card class="kpi-card kpi-hero" shadow="hover">
        <div class="kpi-value" :style="{ color: aqiColor(currentCityLatest.aqi) }">{{ currentCityLatest.aqi ?? '--' }}</div>
        <div class="kpi-label">AQI 指数</div>
        <div class="kpi-level" :style="{ color: aqiColor(currentCityLatest.aqi) }">{{ currentCityLatest.qualityLevel ?? '--' }}</div>
      </el-card>
      <div class="kpi-side">
        <el-card class="kpi-card kpi-small" shadow="hover"><div class="kpi-value-sm" style="color: var(--primary)">{{ currentCityLatest.pm25 != null ? `${currentCityLatest.pm25}` : '--' }}</div><div class="kpi-label">PM2.5 μg/m³</div></el-card>
        <el-card class="kpi-card kpi-small" shadow="hover"><div class="kpi-value-sm" style="color: var(--accent)">{{ currentCityLatest.pm10 != null ? `${currentCityLatest.pm10}` : '--' }}</div><div class="kpi-label">PM10 μg/m³</div></el-card>
        <el-card class="kpi-card kpi-small" shadow="hover"><div class="kpi-value-sm" :style="{ color: riskColor(aqStore.riskResult?.level) }">{{ aqStore.riskResult?.score ?? '--' }}</div><div class="kpi-label">综合风险评分</div></el-card>
      </div>
    </div>

    <HealthAdvice
      v-if="currentCityLatest.aqi"
      :aqi="currentCityLatest.aqi"
      :quality-level="currentCityLatest.qualityLevel"
      :risk-level="aqStore.riskResult?.level"
      :future-summary="aqStore.riskResult?.summary"
      :main-pollutants="(aqStore.riskResult?.drivers || []).slice(0, 3).map(d => d.factor)"
      style="margin: 0 24px"
    />

    <div class="main-grid">
      <div class="grid-left">
        <el-card class="chart-card map-card"><ChinaMap :data="aqStore.mapData" height="520px" @city-click="onMapCityClick" /></el-card>
      </div>
      <div class="grid-right">
        <el-card class="rank-card">
          <template #header><div class="card-header"><span>城市空气质量排名</span><el-button text size="small" @click="toggleRankOrder">{{ rankOrder === 'desc' ? '最优排序' : '最差排序' }}</el-button></div></template>
          <div class="rank-list">
            <div v-for="item in aqStore.rankingList" :key="item.cityId" class="rank-item" @click="onRankCityClick(item.cityId)">
              <span class="rank-num" :class="'rank-' + item.rank">{{ item.rank }}</span>
              <span class="rank-name">{{ item.cityName }}</span>
              <el-tag :type="aqiTagType(item.aqi)" size="small">{{ item.aqi }} {{ item.qualityLevel }}</el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="rank-card" style="margin-top: 12px">
          <template #header><span>未来 5 天风险</span></template>
          <div class="rank-list" style="max-height: 240px">
            <div v-if="!(aqStore.riskResult?.futureRisk || []).length" class="empty-tip">暂无风险数据</div>
            <div v-for="item in (aqStore.riskResult?.futureRisk || []).slice(0, 5)" :key="item.date" class="anomaly-item">
              <el-tag :type="riskTagType(item.level)" size="small">{{ riskLevelText(item.level) }}</el-tag>
              <span class="anomaly-text">{{ item.date }}</span>
              <span class="anomaly-date">{{ item.score }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <AiChatWindow :city-id="cityStore.currentCityId" :city-name="selectedCityName" :context="aiContext" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useCityStore } from '@/stores/city'
import { useAirQualityStore } from '@/stores/airQuality'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import ChinaMap from '@/components/charts/ChinaMap.vue'
import AiChatWindow from '@/components/ai/AiChatWindow.vue'
import HealthAdvice from '@/components/HealthAdvice.vue'

const router = useRouter()
const cityStore = useCityStore()
const aqStore = useAirQualityStore()
const rankOrder = ref('desc')
const selectedCityName = computed(() => cityStore.currentCity?.name || '全国')
const currentCityLatest = computed(() => aqStore.latestData.find((d) => d.cityId === cityStore.currentCityId) || {})

const aiContext = computed(() => ({
  cityName: selectedCityName.value,
  current: currentCityLatest.value,
  prediction: aqStore.predictionResult?.predictions?.slice(0, 5),
  selectedAlgorithm: aqStore.predictionResult?.selectedAlgorithm,
  comparison: aqStore.predictionResult?.comparison || [],
  risk: aqStore.riskResult,
  multiMetricPrediction: aqStore.riskResult?.metricPredictions || {},
  anomalies: aqStore.anomalyList.slice(0, 3).map((a) => ({
    date: a.recordTime.slice(0, 10),
    metric: a.metricName,
    value: a.actualValue,
    severity: a.severity,
    type: a.anomalyType,
  })),
}))

async function loadCityData(cityId) {
  if (!cityId) return
  await Promise.all([
    aqStore.fetchPrediction(cityId, 'aqi', 7, 5, 'moving_average', true),
    aqStore.fetchAnomalyList({ city_id: cityId, limit: 10 }),
    aqStore.fetchRiskAssess(cityId, 5),
  ])
}

function onCityChange(cityId) { cityStore.selectCity(cityId) }
function onMapCityClick({ cityId }) { cityStore.selectCity(cityId) }
function onRankCityClick(cityId) { router.push(`/city/${cityId}`) }
function toggleRankOrder() { rankOrder.value = rankOrder.value === 'desc' ? 'asc' : 'desc'; aqStore.fetchRanking(rankOrder.value, 10) }
function aqiColor(aqi) { if (!aqi) return '#8a8a8a'; if (aqi <= 50) return '#2d6a4f'; if (aqi <= 100) return '#d4a373'; if (aqi <= 150) return '#e07a5f'; if (aqi <= 200) return '#c1121f'; return '#780116' }
function aqiTagType(aqi) { if (aqi <= 50) return 'success'; if (aqi <= 100) return ''; if (aqi <= 200) return 'warning'; return 'danger' }
function riskColor(level) { return ({ low: '#2d6a4f', medium: '#d4a373', high: '#c1121f', severe: '#780116' }[level] || '#8a8a8a') }
function riskLevelText(level) { return ({ low: '低风险', medium: '中风险', high: '高风险', severe: '极高风险' }[level] || level) }
function riskTagType(level) { return ({ low: 'success', medium: 'warning', high: 'danger', severe: 'danger' }[level] || 'info') }

watch(() => cityStore.currentCityId, (newId) => { if (newId) loadCityData(newId) })
onMounted(async () => {
  await cityStore.fetchCities()
  await Promise.all([aqStore.fetchLatest(), aqStore.fetchMapData(), aqStore.fetchRanking('desc', 10)])
  if (cityStore.cities.length > 0 && !cityStore.currentCityId) cityStore.selectCity(cityStore.cities[0].id)
  if (cityStore.currentCityId) loadCityData(cityStore.currentCityId)
})
</script>

<style scoped>
.dashboard { min-height: 100vh; background: var(--bg-page, #eae6e1); }
.kpi-row { display: flex; gap: 16px; padding: 16px 24px 8px; align-items: stretch; }
.kpi-hero { flex: 0 0 220px; text-align: left; padding: 4px; }
.kpi-value { font-size: 48px; font-weight: 800; line-height: 1.1; letter-spacing: -2px; }
.kpi-level { font-size: 14px; font-weight: 700; margin-top: 2px; }
.kpi-label { font-size: 12px; color: var(--text-muted, #8a8a8a); margin-top: 4px; }
.kpi-side { flex: 1; display: grid; grid-template-columns: 1.2fr 1fr 0.8fr; gap: 12px; }
.kpi-small { text-align: left; }
.kpi-value-sm { font-size: 24px; font-weight: 700; line-height: 1.3; }
.main-grid { display: grid; grid-template-columns: 1.8fr 1fr; gap: 12px; padding: 12px 24px 24px; }
.map-card { background: var(--bg-map) !important; border: 1px solid rgba(13, 148, 136, 0.15) !important; overflow: hidden; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.rank-list { display: flex; flex-direction: column; gap: 8px; }
.rank-item, .anomaly-item { display: grid; grid-template-columns: auto 1fr auto; gap: 8px; align-items: center; padding: 8px 10px; border-radius: 10px; background: rgba(255,255,255,0.7); cursor: pointer; }
.rank-num { width: 24px; text-align: center; font-weight: 700; }
.rank-name, .anomaly-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.anomaly-date { font-family: var(--font-mono); }
.empty-tip { font-size: 12px; color: var(--text-muted); padding: 8px 0; }
</style>
