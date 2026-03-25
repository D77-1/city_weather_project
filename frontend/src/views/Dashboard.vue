<template>
  <div class="dashboard">
    <AppHeader @city-change="onCityChange" />

    <!-- KPI 卡片 - 不对称布局 -->
    <div class="kpi-row">
      <el-card class="kpi-card kpi-hero" shadow="hover">
        <div class="kpi-value" :style="{ color: aqiColor(currentCityLatest.aqi) }">{{ currentCityLatest.aqi ?? '--' }}</div>
        <div class="kpi-label">AQI 指数</div>
        <div class="kpi-level" :style="{ color: aqiColor(currentCityLatest.aqi) }">{{ currentCityLatest.qualityLevel ?? '--' }}</div>
      </el-card>
      <div class="kpi-side">
        <el-card class="kpi-card kpi-small" shadow="hover">
          <div class="kpi-value-sm" style="color: var(--primary)">{{ currentCityLatest.pm25 != null ? `${currentCityLatest.pm25}` : '--' }}</div>
          <div class="kpi-label">PM2.5 μg/m³</div>
        </el-card>
        <el-card class="kpi-card kpi-small" shadow="hover">
          <div class="kpi-value-sm" style="color: var(--accent)">{{ currentCityLatest.pm10 != null ? `${currentCityLatest.pm10}` : '--' }}</div>
          <div class="kpi-label">PM10 μg/m³</div>
        </el-card>
        <el-card class="kpi-card kpi-small" shadow="hover">
          <div class="kpi-value-sm" style="color: var(--success)">{{ aqStore.latestData.length || '--' }}</div>
          <div class="kpi-label">在监测的城市</div>
        </el-card>
      </div>
    </div>

    <!-- 天气信息横幅 — 大号 Iconify 图标 + 文字标签 -->
    <div class="weather-bar" v-if="currentCityLatest.temperature != null">
      <div class="weather-item weather-main">
        <Icon :icon="weatherIcon(currentCityLatest.weatherCondition)" width="36" />
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

    <!-- 7日天气预报 — 大号 Iconify 图标 -->
    <div class="forecast-strip" v-if="forecastData.length > 0">
      <div class="fc-item" v-for="f in forecastData" :key="f.date">
        <div class="fc-day">{{ f.weekday }}</div>
        <Icon :icon="weatherIcon(f.weatherText || f.emoji)" width="32" class="fc-icon" />
        <div class="fc-text">{{ f.weatherText }}</div>
        <div class="fc-temp">{{ f.tempMax }}° / {{ f.tempMin }}°</div>
      </div>
    </div>

    <!-- 健康建议横幅 -->
    <HealthAdvice
      v-if="currentCityLatest.aqi"
      :aqi="currentCityLatest.aqi"
      :quality-level="currentCityLatest.qualityLevel"
      style="margin: 0 24px"
    />

    <!-- 实时真实 AQI 数据（Open-Meteo CAMS） -->
    <div class="realtime-aqi-bar" v-if="realtimeAqi">
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

    <!-- 主体两栏布局 — 不对称: 地图(宽) + 排名/异常(窄) -->
    <div class="main-grid">
      <!-- 左栏: 中国地图 -->
      <div class="grid-left">
        <el-card class="chart-card map-card">
          <ChinaMap :data="aqStore.mapData" height="520px" @city-click="onMapCityClick" />
        </el-card>
      </div>

      <!-- 右栏: 排名 + 异常列表 — 信息密度更高 -->
      <div class="grid-right">
        <el-card class="rank-card">
          <template #header>
            <div class="card-header">
              <span>城市空气质量排名</span>
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

        <el-card class="rank-card" style="margin-top: 12px">
          <template #header><span>近期异常记录</span></template>
          <div class="rank-list" style="max-height: 240px">
            <div v-if="aqStore.anomalyList.length === 0" class="empty-tip">暂无异常数据</div>
            <div v-for="a in aqStore.anomalyList.slice(0, 8)" :key="a.id" class="anomaly-item">
              <el-tag :type="a.severity === 'severe' ? 'danger' : a.severity === 'moderate' ? 'warning' : 'info'" size="small">
                {{ { severe: '严重', moderate: '中度', mild: '轻度' }[a.severity] || a.severity }}
              </el-tag>
              <span class="anomaly-text">{{ a.metricName.toUpperCase() }} = {{ a.actualValue }}</span>
              <span class="anomaly-date">{{ a.recordTime.slice(5, 10) }}</span>
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
import { weatherApi, realAqiApi } from '@/api/modules'
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
const selectedCityName = computed(() => cityStore.currentCity?.name || '全国')

const currentCityLatest = computed(() =>
  aqStore.latestData.find((d) => d.cityId === cityStore.currentCityId) || {}
)

const aiContext = computed(() => ({
  cityName: selectedCityName.value,
  current: currentCityLatest.value,
  prediction: aqStore.predictionResult?.predictions?.slice(0, 5),
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
    aqStore.fetchAnomalyList({ city_id: cityId, limit: 10 }),
  ])
  weatherApi.getRealtime(cityId).then(d => { realtimeWeather.value = d }).catch(() => {})
  weatherApi.getForecast(cityId, 7).then(d => { forecastData.value = d.forecast || [] }).catch(() => {})
  realAqiApi.getRealtime(cityId).then(d => { realtimeAqi.value = d }).catch(() => {})
}

function onCityChange(cityId) { cityStore.selectCity(cityId) }
function onMapCityClick({ cityId }) { cityStore.selectCity(cityId) }
function onRankCityClick(cityId) { router.push(`/city/${cityId}`) }

function toggleRankOrder() {
  rankOrder.value = rankOrder.value === 'desc' ? 'asc' : 'desc'
  aqStore.fetchRanking(rankOrder.value, 10)
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

watch(() => cityStore.currentCityId, (newId) => {
  if (newId) loadCityData(newId)
})

onMounted(async () => {
  await cityStore.fetchCities()
  await Promise.all([
    aqStore.fetchLatest(),
    aqStore.fetchMapData(),
    aqStore.fetchRanking('desc', 10),
  ])
  if (cityStore.cities.length > 0 && !cityStore.currentCityId) {
    cityStore.selectCity(cityStore.cities[0].id)
  }
  // 切页回来时 currentCityId 已存在但 watch 不会再触发，手动加载
  if (cityStore.currentCityId) {
    loadCityData(cityStore.currentCityId)
  }
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--bg-page, #eae6e1);
  transition: background-color 0.4s var(--bounce);
}

/* KPI 不对称布局 */
.kpi-row {
  display: flex;
  gap: 16px;
  padding: 16px 24px 8px;
  align-items: stretch;
}
.kpi-hero {
  flex: 0 0 220px;
  text-align: left;
  padding: 4px;
}
.kpi-value {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -2px;
}
.kpi-level {
  font-size: 14px;
  font-weight: 700;
  margin-top: 2px;
}
.kpi-label {
  font-size: 12px;
  color: var(--text-muted, #8a8a8a);
  margin-top: 4px;
}
.kpi-side {
  flex: 1;
  display: grid;
  grid-template-columns: 1.2fr 1fr 0.8fr;
  gap: 12px;
}
.kpi-small {
  text-align: left;
}
.kpi-value-sm {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.3;
}

/* 天气栏 — 大号图标 */
.weather-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin: 0 24px 8px;
  padding: 12px 20px;
  background: var(--bg-card);
  border-radius: 14px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-color);
}
.weather-item { display: flex; align-items: center; gap: 8px; }
.weather-item div { display: flex; flex-direction: column; }
.weather-main { gap: 10px; }
.weather-main-text { display: flex; flex-direction: column; }
.weather-cond { font-size: 15px; font-weight: 700; color: var(--text-primary); }
.weather-temp { font-size: 20px; font-weight: 800; color: var(--primary); font-family: var(--font-mono); }
.weather-label { font-size: 10px; color: var(--text-muted); }
.weather-val { font-size: 14px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.weather-divider { width: 1px; height: 32px; background: var(--border-color); }
.realtime-tag { background: rgba(13,148,136,0.06); padding: 6px 12px; border-radius: 12px; border: 1px solid rgba(13,148,136,0.2); }

/* 7日预报 — 大号图标 */
.forecast-strip {
  display: flex;
  gap: 6px;
  margin: 0 24px 8px;
  padding: 12px 16px;
  background: var(--bg-card);
  border-radius: 14px;
  box-shadow: var(--shadow);
  border: 1px solid var(--border-color);
  overflow-x: auto;
}
.fc-item { flex: 1; min-width: 70px; text-align: center; }
.fc-day { font-size: 11px; color: var(--text-muted); }
.fc-icon { margin: 4px 0; color: var(--primary); }
.fc-text { font-size: 10px; color: var(--text-secondary); }
.fc-temp { font-size: 13px; font-weight: 700; color: var(--text-primary); font-family: var(--font-mono); }

/* 实时真实 AQI 条 */
.realtime-aqi-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin: 8px 24px;
  padding: 10px 20px;
  background: linear-gradient(135deg, rgba(13,148,136,0.08), rgba(224,122,95,0.06));
  border: 1px solid var(--primary);
  border-radius: 14px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(8px);
  flex-wrap: wrap;
}
.ra-badge {
  background: var(--primary);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 10px;
  white-space: nowrap;
}
.ra-item { display: flex; flex-direction: column; align-items: center; min-width: 50px; }
.ra-label { font-size: 11px; color: var(--text-muted, #8a8a8a); }
.ra-val { font-size: 16px; font-weight: 700; color: var(--text-primary, #2c2c2c); }
.ra-source { margin-left: auto; font-size: 10px; color: var(--text-muted, #8a8a8a); white-space: nowrap; }

/* 主体两栏 — 不对称 */
.main-grid {
  display: grid;
  grid-template-columns: 1.8fr 1fr;
  gap: 12px;
  padding: 12px 24px 24px;
}

/* 地图卡片 — 渐变过渡消除突兀感 */
.map-card {
  background: var(--bg-map) !important;
  border: 1px solid rgba(13, 148, 136, 0.15) !important;
  overflow: hidden;
  position: relative;
}
.map-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at center, transparent 60%, var(--bg-page) 100%);
  pointer-events: none;
  z-index: 1;
  opacity: 0.3;
}

.card-header { display: flex; justify-content: space-between; align-items: center; }
.rank-list { max-height: 400px; overflow-y: auto; }
.rank-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 0; cursor: pointer;
  border-bottom: 1px solid var(--border-color, #d5cfc7);
  transition: background 0.3s var(--bounce);
}
.rank-item:hover { background: rgba(13, 148, 136, 0.06); }
.rank-num {
  width: 22px; height: 22px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; background: #d5cfc7; color: #5a5a5a;
}
.rank-1 { background: var(--danger); color: #fff; }
.rank-2 { background: var(--accent); color: #fff; }
.rank-3 { background: var(--primary); color: #fff; }
.rank-name { flex: 1; font-size: 13px; color: var(--text-primary, #2c2c2c); }

.anomaly-item { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 12px; }
.anomaly-text { flex: 1; color: var(--text-primary, #2c2c2c); }
.anomaly-date { color: var(--text-muted, #8a8a8a); }
.empty-tip { text-align: center; color: var(--text-muted); padding: 20px; }
</style>
