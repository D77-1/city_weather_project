<template>
  <div class="dashboard page-shell">
    <AppHeader @city-change="onCityChange" />

    <section class="hero-section">
      <div class="hero-copy panel-surface">
        <div class="hero-eyebrow">National Air Quality Overview</div>
        <div class="hero-title-row">
          <div>
            <h2 class="hero-title">全国空气质量态势总览</h2>
            <p class="hero-subtitle">以城市监测、气象变化和异常波动为核心，快速查看当前城市的污染等级、天气背景与重点关注信息。</p>
          </div>
          <div class="hero-city-chip">
            <span class="hero-chip-label">当前对象</span>
            <span class="hero-chip-value">{{ selectedCityName }}</span>
          </div>
        </div>
      </div>

      <div class="hero-status-grid">
        <el-card class="kpi-card kpi-hero" shadow="hover">
          <div class="hero-kpi-top">
            <span class="kpi-trend">实时监测</span>
          </div>
          <div class="kpi-value" :style="{ color: aqiColor(currentCityLatest.aqi) }">{{ currentCityLatest.aqi ?? '--' }}</div>
          <div class="kpi-label">AQI 指数</div>
          <div class="kpi-level" :style="{ color: aqiColor(currentCityLatest.aqi) }">{{ currentCityLatest.qualityLevel ?? '--' }}</div>
        </el-card>

        <div class="kpi-side">
          <el-card class="kpi-card kpi-small" shadow="hover">
            <div class="kpi-label">PM2.5</div>
            <div class="kpi-value-sm" style="color: var(--primary)">{{ currentCityLatest.pm25 != null ? `${currentCityLatest.pm25}` : '--' }}</div>
            <div class="kpi-label"> μg/m³</div>
          </el-card>
          <el-card class="kpi-card kpi-small" shadow="hover">
            <div class="kpi-label">PM10</div>
            <div class="kpi-value-sm" style="color: var(--accent)">{{ currentCityLatest.pm10 != null ? `${currentCityLatest.pm10}` : '--' }}</div>
            <div class="kpi-label">μg/m³</div>
          </el-card>
          <el-card class="kpi-card kpi-small" shadow="hover">
            <div class="kpi-value-sm" style="color: var(--success)">{{ aqStore.latestData.length ?? '--' }}</div>
            <div class="kpi-label">在监测的城市</div>
          </el-card>
        </div>
      </div>
    </section>

    <div class="weather-bar panel-surface" v-if="currentCityLatest.temperature != null">
      <div class="weather-item weather-main">
        <div class="weather-icon-wrap">
          <Icon :icon="weatherIcon(currentCityLatest.weatherCondition)" width="38" />
        </div>
        <div class="weather-main-text">
          <span class="weather-cond">{{ currentCityLatest.weatherCondition || '--' }}</span>
          <span class="weather-temp">{{ currentCityLatest.temperature }}℃</span>
        </div>
      </div>
      <div class="weather-divider"></div>
      <div class="weather-item">
        <Icon icon="meteocons:humidity-fill" width="22" />
        <div><span class="weather-val">{{ currentCityLatest.humidity }}%</span><span class="weather-label">湿度</span></div>
      </div>
      <div class="weather-item">
        <Icon icon="meteocons:wind-fill" width="22" />
        <div><span class="weather-val">{{ currentCityLatest.windDirection }} {{ currentCityLatest.windSpeed }}m/s</span><span class="weather-label">风力</span></div>
      </div>
      <div class="weather-item" v-if="currentCityLatest.rainfall > 0">
        <Icon icon="meteocons:raindrops-fill" width="22" />
        <div><span class="weather-val">{{ currentCityLatest.rainfall }}mm</span><span class="weather-label">降水</span></div>
      </div>
      <template v-if="realtimeWeather">
        <div class="weather-divider"></div>
        <div class="weather-item realtime-tag">
          <Icon :icon="weatherIcon(realtimeWeather.weatherText)" width="28" />
          <div>
            <span class="weather-val">{{ realtimeWeather.weatherText }} {{ realtimeWeather.temperature }}℃</span>
            <span class="weather-label">Open-Meteo 实时</span>
          </div>
        </div>
      </template>
    </div>

    <div class="forecast-strip panel-surface" v-if="forecastData.length > 0">
      <div class="strip-head">
        <span class="panel-kicker">7-Day Weather Window</span>
        <span class="strip-tip">辅助理解天气背景与空气质量变化</span>
      </div>
      <div class="forecast-scroll">
        <div class="fc-item" v-for="f in forecastData" :key="f.date">
          <div class="fc-day">{{ f.weekday }}</div>
          <Icon :icon="weatherIcon(f.weatherText || f.emoji)" width="32" class="fc-icon" />
          <div class="fc-text">{{ f.weatherText }}</div>
          <div class="fc-temp">{{ f.tempMax }}° / {{ f.tempMin }}°</div>
        </div>
      </div>
    </div>

    <HealthAdvice
      v-if="currentCityLatest.aqi != null"
      :aqi="currentCityLatest.aqi"
      :quality-level="currentCityLatest.qualityLevel"
      style="margin: 0 24px"
    />

    <div class="realtime-aqi-bar panel-surface" v-if="realtimeAqi">
      <div class="ra-badge">实时真实数据</div>
      <div class="ra-item">
        <span class="ra-label">AQI</span>
        <span class="ra-val" :style="{ color: aqiColor(realtimeAqi.aqi) }">{{ realtimeAqi.aqi }}</span>
      </div>
      <div class="ra-item">
        <span class="ra-label">PM2.5</span>
        <span class="ra-val">{{ realtimeAqi.pm25 }}</span>
      </div>
      <div class="ra-item">
        <span class="ra-label">PM10</span>
        <span class="ra-val">{{ realtimeAqi.pm10 }}</span>
      </div>
      <div class="ra-item">
        <span class="ra-label">NO₂</span>
        <span class="ra-val">{{ realtimeAqi.no2 }}</span>
      </div>
      <div class="ra-item">
        <span class="ra-label">O₃</span>
        <span class="ra-val">{{ realtimeAqi.o3 }}</span>
      </div>
      <div class="ra-item">
        <span class="ra-label">等级</span>
        <span class="ra-val">{{ realtimeAqi.qualityLevel }}</span>
      </div>
      <div class="ra-source">来源: {{ realtimeAqi.source }}</div>
    </div>

    <div class="main-grid">
      <div class="grid-left">
        <el-card class="chart-card map-card panel-frame">
          <template #header>
            <div class="panel-headline">
              <div>
                <span class="panel-kicker">Spatial Monitoring</span>
                <h3>全国空气质量空间分布</h3>
              </div>
              <span class="panel-tip">点击地图中的城市进入详情页</span>
            </div>
          </template>
          <ChinaMap :data="aqStore.mapData" height="520px" @city-click="onMapCityClick" />
        </el-card>
      </div>

      <div class="grid-right">
        <el-card class="rank-card panel-frame">
          <template #header>
            <div class="card-header">
              <div>
                <span class="panel-kicker">Ranking Monitor</span>
                <h3>城市空气质量排名</h3>
              </div>
              <el-button text size="small" @click="toggleRankOrder">
                {{ rankOrder === 'desc' ? '最优排序' : '最差排序' }}
              </el-button>
            </div>
          </template>
          <div class="rank-list">
            <div
              v-for="item in aqStore.rankingList"
              :key="item.cityId"
              class="rank-item"
              @click="onRankCityClick(item.cityId)"
            >
              <span class="rank-num" :class="'rank-' + item.rank">{{ item.rank }}</span>
              <span class="rank-name">{{ item.cityName }}</span>
              <el-tag :type="aqiTagType(item.aqi)" size="small">{{ item.aqi }} {{ item.qualityLevel }}</el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="rank-card panel-frame anomaly-panel">
          <template #header>
            <div class="card-header">
              <div>
                <span class="panel-kicker">Abnormal Signal</span>
                <h3>近期异常记录</h3>
              </div>
            </div>
          </template>
          <div class="rank-list anomaly-list" style="max-height: 240px">
            <div v-if="aqStore.anomalyList.length === 0" class="empty-tip">暂无异常数据</div>
            <div v-for="a in aqStore.anomalyList.slice(0, 8)" :key="a.id" class="anomaly-item">
              <el-tag :type="a.severity === 'severe' ? 'danger' : a.severity === 'moderate' ? 'warning' : 'info'" size="small">
                {{ { severe: '严重', moderate: '中度', mild: '轻度' }[a.severity] || a.severity }}
              </el-tag>
              <span class="anomaly-text">{{ formatMetricName(a.metricName) }} = {{ a.actualValue }}</span>
              <span class="anomaly-date">{{ formatMonthDay(a.recordTime) }}</span>
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
import { anomalyApi, weatherApi, realAqiApi } from '@/api/modules'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import ChinaMap from '@/components/charts/ChinaMap.vue'
import AiChatWindow from '@/components/ai/AiChatWindow.vue'
import HealthAdvice from '@/components/HealthAdvice.vue'

const router = useRouter()
const cityStore = useCityStore()
const aqStore = useAirQualityStore()

const rankOrder = ref('desc')
const realtimeWeather = ref(null)
const forecastData = ref([])
const realtimeAqi = ref(null)
const cityRequestToken = ref(0)

function resetCityDependentData() {
  realtimeWeather.value = null
  forecastData.value = []
  realtimeAqi.value = null
}

function formatMetricName(metricName) {
  return typeof metricName === 'string' ? metricName.toUpperCase() : '--'
}

function formatRecordDate(recordTime) {
  return typeof recordTime === 'string' ? recordTime.slice(0, 10) : '--'
}

function formatMonthDay(recordTime) {
  const dateText = formatRecordDate(recordTime)
  return dateText !== '--' ? dateText.slice(5, 10) : '--'
}

function buildAiAnomalies(anomalies) {
  return anomalies.slice(0, 3).map((a) => ({
    date: formatRecordDate(a.recordTime),
    metric: a.metricName ?? '--',
    value: a.actualValue,
    severity: a.severity,
    type: a.anomalyType,
  }))
}

async function syncCityData(cityId) {
  if (!cityId) {
    cityRequestToken.value += 1
    resetCityDependentData()
    aqStore.anomalyList = []
    return
  }
  const requestToken = ++cityRequestToken.value
  resetCityDependentData()
  const anomalies = await anomalyApi.getList({ city_id: cityId, limit: 10 })
  if (requestToken !== cityRequestToken.value || cityId !== cityStore.currentCityId) return
  aqStore.anomalyList = anomalies
  weatherApi.getRealtime(cityId)
    .then((data) => {
      if (requestToken === cityRequestToken.value && cityId === cityStore.currentCityId) {
        realtimeWeather.value = data
      }
    })
    .catch(() => {})
  weatherApi.getForecast(cityId, 7)
    .then((data) => {
      if (requestToken === cityRequestToken.value && cityId === cityStore.currentCityId) {
        forecastData.value = data.forecast || []
      }
    })
    .catch(() => {})
  realAqiApi.getRealtime(cityId)
    .then((data) => {
      if (requestToken === cityRequestToken.value && cityId === cityStore.currentCityId) {
        realtimeAqi.value = data
      }
    })
    .catch(() => {})
}

const selectedCityName = computed(() => cityStore.currentCity?.name || '全国')

const currentCityLatest = computed(() =>
  aqStore.latestData.find((d) => d.cityId === cityStore.currentCityId) || {}
)

const aiContext = computed(() => ({
  cityName: selectedCityName.value,
  current: currentCityLatest.value,
  prediction: aqStore.predictionResult?.predictions?.slice(0, 5),
  anomalies: buildAiAnomalies(aqStore.anomalyList),
}))

async function ensureInitialData() {
  await cityStore.fetchCities()
  await Promise.all([
    aqStore.fetchLatest(),
    aqStore.fetchMapData(),
    aqStore.fetchRanking(rankOrder.value, 10),
  ])
  if (cityStore.cities.length > 0 && !cityStore.currentCityId) {
    cityStore.selectCity(cityStore.cities[0].id)
  } else if (cityStore.currentCityId) {
    await syncCityData(cityStore.currentCityId)
  }
}

async function loadCityData(cityId) {
  await syncCityData(cityId)
}

function onCityChange(cityId) { cityStore.selectCity(cityId) }
function onMapCityClick({ cityId }) { cityStore.selectCity(cityId) }
function onRankCityClick(cityId) { router.push(`/city/${cityId}`) }

function toggleRankOrder() {
  rankOrder.value = rankOrder.value === 'desc' ? 'asc' : 'desc'
  aqStore.fetchRanking(rankOrder.value, 10)
}

function aqiColor(aqi) {
  if (aqi == null) return '#8a8a8a'
  if (aqi <= 50) return '#32d296'
  if (aqi <= 100) return '#f0b65a'
  if (aqi <= 150) return '#ff9e64'
  if (aqi <= 200) return '#ff6b81'
  return '#cf3c6d'
}

function aqiTagType(aqi) {
  if (aqi <= 50) return 'success'
  if (aqi <= 100) return ''
  if (aqi <= 200) return 'warning'
  return 'danger'
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

watch(() => cityStore.currentCityId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadCityData(newId)
  }
  if (!newId) {
    cityRequestToken.value += 1
    resetCityDependentData()
  }
})

onMounted(async () => {
  await ensureInitialData()
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: transparent;
  transition: background-color 0.4s var(--bounce);
}

.page-shell {
  position: relative;
  padding-bottom: 24px;
}

.panel-surface {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(10, 22, 37, 0.86), rgba(8, 18, 31, 0.72));
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
}

.panel-surface::before,
.panel-frame::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(127, 246, 234, 0.08), transparent 30%, transparent 70%, rgba(110, 168, 255, 0.08));
  pointer-events: none;
}

.hero-section {
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 16px;
  padding: 18px 24px 10px;
}

.hero-copy {
  border-radius: 28px;
  padding: 28px;
}

.hero-eyebrow,
.panel-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--primary-light);
}

.hero-eyebrow::before,
.panel-kicker::before {
  content: '';
  width: 18px;
  height: 1px;
  background: currentColor;
  opacity: 0.75;
}

.hero-title-row {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-top: 20px;
}

.hero-title {
  font-size: clamp(28px, 4vw, 42px);
  line-height: 1.08;
  letter-spacing: 0.02em;
  color: var(--text-primary);
}

.hero-subtitle {
  margin-top: 14px;
  max-width: 720px;
  line-height: 1.8;
  color: var(--text-secondary);
}

.hero-city-chip {
  align-self: flex-start;
  min-width: 144px;
  padding: 16px 18px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: rgba(7, 18, 31, 0.72);
}

.hero-chip-label {
  display: block;
  font-size: 10px;
  letter-spacing: 0.2em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.hero-chip-value {
  display: block;
  margin-top: 8px;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.hero-status-grid {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: 12px;
}

.kpi-card {
  position: relative;
  min-height: 100%;
}

.kpi-hero {
  padding: 26px 24px;
  border-radius: 28px;
}

.hero-kpi-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.kpi-trend {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(39, 211, 195, 0.12);
  color: var(--primary-light);
  font-size: 11px;
}

.kpi-value {
  font-size: clamp(52px, 6vw, 70px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.05em;
}

.kpi-level {
  margin-top: 8px;
  font-size: 16px;
  font-weight: 700;
}

.kpi-label {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.kpi-side {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.kpi-small {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.kpi-value-sm {
  margin-top: 20px;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.weather-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin: 0 24px 10px;
  padding: 16px 22px;
  border-radius: 24px;
  flex-wrap: wrap;
}

.weather-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.weather-item div {
  display: flex;
  flex-direction: column;
}

.weather-main {
  gap: 12px;
}

.weather-icon-wrap {
  display: grid;
  place-items: center;
  width: 54px;
  height: 54px;
  border-radius: 18px;
  background: rgba(39, 211, 195, 0.08);
  color: var(--primary-light);
}

.weather-cond {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.weather-temp {
  font-size: 22px;
  font-weight: 800;
  color: var(--primary-light);
  font-family: var(--font-mono);
}

.weather-label {
  font-size: 11px;
  color: var(--text-muted);
}

.weather-val {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.weather-divider {
  width: 1px;
  height: 34px;
  background: var(--border-color);
}

.realtime-tag {
  padding: 8px 12px;
  border-radius: 16px;
  border: 1px solid rgba(39, 211, 195, 0.18);
  background: rgba(39, 211, 195, 0.08);
}

.forecast-strip {
  margin: 0 24px 10px;
  padding: 18px 20px;
  border-radius: 24px;
}

.strip-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.strip-tip {
  font-size: 12px;
  color: var(--text-muted);
}

.forecast-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 2px;
}

.fc-item {
  flex: 1;
  min-width: 88px;
  padding: 14px 12px;
  text-align: center;
  border-radius: 18px;
  background: rgba(7, 18, 31, 0.6);
  border: 1px solid rgba(124, 154, 188, 0.14);
}

.fc-day {
  font-size: 11px;
  color: var(--text-muted);
}

.fc-icon {
  margin: 8px 0 6px;
  color: var(--primary-light);
}

.fc-text {
  font-size: 11px;
  color: var(--text-secondary);
}

.fc-temp {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-mono);
}

.realtime-aqi-bar {
  display: flex;
  align-items: center;
  gap: 18px;
  margin: 10px 24px;
  padding: 14px 20px;
  border-radius: 24px;
  border: 1px solid rgba(39, 211, 195, 0.24);
  background: linear-gradient(135deg, rgba(39, 211, 195, 0.1), rgba(110, 168, 255, 0.08));
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
  flex-wrap: wrap;
}

.ra-badge {
  padding: 5px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: #03111d;
  font-size: 11px;
  font-weight: 800;
}

.ra-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 56px;
}

.ra-label {
  font-size: 11px;
  color: var(--text-muted);
}

.ra-val {
  font-size: 17px;
  font-weight: 700;
  color: var(--text-primary);
}

.ra-source {
  margin-left: auto;
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
}

.main-grid {
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  gap: 14px;
  padding: 12px 24px 24px;
}

.panel-frame {
  position: relative;
  overflow: hidden;
}

.panel-headline,
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.panel-headline h3,
.card-header h3 {
  margin-top: 6px;
  font-size: 20px;
  color: var(--text-primary);
}

.panel-tip {
  font-size: 12px;
  color: var(--text-muted);
}

.map-card {
  background: linear-gradient(180deg, rgba(7, 17, 31, 0.96), rgba(7, 16, 28, 0.92)) !important;
  border: 1px solid rgba(39, 211, 195, 0.18) !important;
}

.map-card::after {
  content: '';
  position: absolute;
  inset: auto 0 0 0;
  height: 120px;
  background: linear-gradient(180deg, transparent, rgba(4, 9, 18, 0.52));
  pointer-events: none;
}

.rank-card + .rank-card {
  margin-top: 14px;
}

.rank-list {
  max-height: 400px;
  overflow-y: auto;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  cursor: pointer;
  border-bottom: 1px solid rgba(124, 154, 188, 0.12);
  transition: background 0.3s var(--bounce), padding-left 0.3s var(--bounce);
}

.rank-item:hover {
  background: rgba(39, 211, 195, 0.06);
  padding-left: 6px;
}

.rank-num {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: rgba(124, 154, 188, 0.16);
  color: var(--text-secondary);
}

.rank-1 {
  background: rgba(255, 107, 129, 0.2);
  color: #ffd7de;
}

.rank-2 {
  background: rgba(240, 182, 90, 0.2);
  color: #ffe7bd;
}

.rank-3 {
  background: rgba(39, 211, 195, 0.2);
  color: #d8fffb;
}

.rank-name {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
}

.anomaly-list {
  padding-right: 4px;
}

.anomaly-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 12px;
}

.anomaly-text {
  flex: 1;
  color: var(--text-primary);
}

.anomaly-date {
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.empty-tip {
  text-align: center;
  color: var(--text-muted);
  padding: 20px;
}

@media (max-width: 1180px) {
  .hero-section,
  .main-grid {
    grid-template-columns: 1fr;
  }

  .hero-status-grid {
    grid-template-columns: 1fr;
  }

  .kpi-side {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero-section,
  .main-grid {
    padding-left: 14px;
    padding-right: 14px;
  }

  .weather-bar,
  .forecast-strip,
  .realtime-aqi-bar {
    margin-left: 14px;
    margin-right: 14px;
  }

  .hero-copy {
    padding: 22px 18px;
  }

  .hero-title-row,
  .strip-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .kpi-side {
    grid-template-columns: 1fr;
  }

  .weather-divider {
    display: none;
  }

  .ra-source {
    margin-left: 0;
  }
}
</style>
