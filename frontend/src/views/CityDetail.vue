<template>
  <div class="city-detail">
    <AppHeader @city-change="onCityChange" />

    <div class="detail-content" v-loading="loading">
      <el-page-header @back="$router.push('/')" style="padding: 16px 24px 0">
        <template #content>
          <span class="page-title">{{ city?.name }} 空气质量详情</span>
        </template>
      </el-page-header>

      <!-- 顶部 KPI - 不对称: AQI大卡 + 6小卡 -->
      <div class="kpi-row" v-if="latestCity">
        <div class="kpi-hero" :style="{ borderLeftColor: aqiColor(latestCity.aqi) }">
          <div class="kpi-big" :style="{ color: aqiColor(latestCity.aqi) }">{{ latestCity.aqi }}</div>
          <div class="kpi-sub">AQI · {{ latestCity.qualityLevel }}</div>
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

      <!-- 健康建议横幅 -->
      <HealthAdvice v-if="latestCity" :aqi="latestCity.aqi" :quality-level="latestCity.qualityLevel" style="margin: 0 24px" />

      <!-- 天气信息卡片 -->
      <div class="weather-section" v-if="latestCity && latestCity.temperature != null">
        <el-card class="weather-card">
          <template #header><span>当前天气</span></template>
          <div class="weather-grid">
            <div class="weather-cell main-weather">
              <Icon :icon="weatherIcon(latestCity.weatherCondition)" width="36" />
              <span class="weather-cond">{{ latestCity.weatherCondition || '--' }}</span>
            </div>
            <div class="weather-cell">
              <div class="w-num">{{ latestCity.temperature }}<small>℃</small></div>
              <div class="w-label">温度</div>
            </div>
            <div class="weather-cell">
              <div class="w-num">{{ latestCity.humidity }}<small>%</small></div>
              <div class="w-label">湿度</div>
            </div>
            <div class="weather-cell">
              <div class="w-num">{{ latestCity.windSpeed }}<small>m/s</small></div>
              <div class="w-label">{{ latestCity.windDirection }}风</div>
            </div>
            <div class="weather-cell">
              <div class="w-num">{{ latestCity.rainfall }}<small>mm</small></div>
              <div class="w-label">降水量</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 实时真实 AQI (Open-Meteo CAMS) -->
      <el-card class="realtime-card" v-if="realtimeAqi" style="margin: 8px 24px">
        <template #header>
          <div class="card-header">
            <span>实时真实空气质量</span>
            <el-tag type="success" size="small" effect="plain">{{ realtimeAqi.source }}</el-tag>
          </div>
        </template>
        <div class="realtime-grid">
          <div class="rt-cell rt-hero" :style="{ borderLeftColor: aqiColor(realtimeAqi.aqi) }">
            <div class="rt-aqi" :style="{ color: aqiColor(realtimeAqi.aqi) }">{{ realtimeAqi.aqi }}</div>
            <div class="rt-level">{{ realtimeAqi.qualityLevel }}</div>
          </div>
          <div class="rt-cell"><div class="rt-val">{{ realtimeAqi.pm25 }}</div><div class="rt-lbl">PM2.5</div></div>
          <div class="rt-cell"><div class="rt-val">{{ realtimeAqi.pm10 }}</div><div class="rt-lbl">PM10</div></div>
          <div class="rt-cell"><div class="rt-val">{{ realtimeAqi.so2 }}</div><div class="rt-lbl">SO₂</div></div>
          <div class="rt-cell"><div class="rt-val">{{ realtimeAqi.no2 }}</div><div class="rt-lbl">NO₂</div></div>
          <div class="rt-cell"><div class="rt-val">{{ realtimeAqi.co }}</div><div class="rt-lbl">CO</div></div>
          <div class="rt-cell"><div class="rt-val">{{ realtimeAqi.o3 }}</div><div class="rt-lbl">O₃</div></div>
        </div>
        <div v-if="realtimeAqi.primaryPollutant" style="margin-top:8px; font-size:12px; color: var(--text-muted)">
          首要污染物: <b style="color: var(--danger)">{{ realtimeAqi.primaryPollutant }}</b> · 数据按国标 HJ 633-2012 计算
        </div>
      </el-card>

      <!-- 未来5日 AQI 预报 (真实数据) -->
      <el-card style="margin: 0 24px 8px" v-if="aqiForecast.length > 0">
        <template #header>
          <div class="card-header">
            <span>未来空气质量预报</span>
            <el-tag size="small" effect="plain">Open-Meteo CAMS</el-tag>
          </div>
        </template>
        <div class="forecast-row">
          <div class="fc-card" v-for="f in aqiForecast" :key="f.date">
            <div class="fc-day">{{ f.dateShort }}</div>
            <div class="fc-aqi" :style="{ color: aqiColor(f.aqi) }">{{ f.aqi }}</div>
            <div class="fc-text">{{ f.qualityLevel }}</div>
            <div class="fc-extra">PM2.5: {{ f.pm25 }}</div>
          </div>
        </div>
      </el-card>

      <!-- 基本信息 -->
      <el-descriptions :column="5" border style="margin: 12px 24px" size="small">
        <el-descriptions-item label="省份">{{ city?.province }}</el-descriptions-item>
        <el-descriptions-item label="城市编码">{{ city?.cityCode }}</el-descriptions-item>
        <el-descriptions-item label="城市等级">{{ city?.cityLevel }}</el-descriptions-item>
        <el-descriptions-item label="常住人口">{{ city?.population ? city.population + ' 万' : '--' }}</el-descriptions-item>
        <el-descriptions-item label="监测站点">
          <el-tag v-for="s in stations" :key="s.id" size="small" class="station-tag">{{ s.stationName }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 主图表区 - 不对称 -->
      <div class="charts-grid">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>AQI 走势 + 预测</span>
              <el-radio-group v-model="days" size="small" @change="onDaysChange">
                <el-radio-button :value="30">30天</el-radio-button>
                <el-radio-button :value="60">60天</el-radio-button>
                <el-radio-button :value="90">90天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <TrendLine :trend-data="combinedTrend" :title="`${city?.name || ''} AQI 走势`" height="350px" />
        </el-card>

        <el-card>
          <RadarChart :pollutant-data="pollutants" :city-name="city?.name || ''" height="350px" />
        </el-card>
      </div>

      <!-- 第二行 - 不对称 -->
      <div class="charts-grid" style="margin-top: 0">
        <!-- 污染物浓度 vs 国标 -->
        <el-card>
          <template #header><span>达标了吗？</span></template>
          <el-table :data="pollutantTable" stripe size="small" style="width: 100%">
            <el-table-column prop="name" label="污染物" width="90" />
            <el-table-column prop="value" label="当前值" width="90">
              <template #default="{ row }">
                <span :style="{ color: row.value > row.limit ? 'var(--danger)' : 'var(--success)', fontWeight: 600 }">{{ row.value }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="unit" label="单位" width="80" />
            <el-table-column prop="limit" label="国标限值" width="90" />
            <el-table-column label="达标?" width="90">
              <template #default="{ row }">
                <el-tag :type="row.value <= row.limit ? 'success' : 'danger'" size="small">
                  {{ row.value <= row.limit ? '达标' : '超了' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="占比">
              <template #default="{ row }">
                <el-progress
                  :percentage="Math.min(100, Math.round((row.value / row.limit) * 100))"
                  :color="row.value > row.limit ? 'var(--danger)' : 'var(--success)'"
                  :stroke-width="12"
                />
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- IQR 异常检测 -->
        <el-card>
          <template #header><span>最近异常记录</span></template>
          <div v-if="aqStore.anomalyResult">
            <div class="iqr-visual">
              <div class="iqr-bar-track">
                <div class="iqr-zone normal" :style="iqrBarStyle.normal" />
                <div class="iqr-zone iqr-box" :style="iqrBarStyle.box">
                  <span class="iqr-label">Q1: {{ aqStore.anomalyResult.q1 }}</span>
                  <span class="iqr-label">Q3: {{ aqStore.anomalyResult.q3 }}</span>
                </div>
              </div>
              <div class="iqr-meta">
                <span>下界: {{ aqStore.anomalyResult.lower_bound }}</span>
                <span>IQR: {{ aqStore.anomalyResult.iqr }}</span>
                <span>上界: {{ aqStore.anomalyResult.upper_bound }}</span>
              </div>
            </div>

            <el-divider />

            <el-row :gutter="16">
              <el-col :span="8">
                <el-statistic title="数据点" :value="aqStore.anomalyResult.total_points" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="异常数" :value="aqStore.anomalyResult.anomaly_count">
                  <template #suffix>
                    <el-tag type="danger" size="small" v-if="aqStore.anomalyResult.anomaly_count > 0">需关注</el-tag>
                  </template>
                </el-statistic>
              </el-col>
              <el-col :span="8">
                <el-statistic title="异常占比" :value="anomalyRatio" suffix="%" />
              </el-col>
            </el-row>

            <el-table
              v-if="aqStore.anomalyResult.anomalies?.length > 0"
              :data="aqStore.anomalyResult.anomalies"
              stripe size="small"
              style="margin-top: 12px"
              max-height="200"
            >
              <el-table-column prop="date" label="日期" width="100" />
              <el-table-column prop="value" label="数值" width="80">
                <template #default="{ row }">
                  <span style="color: var(--danger); font-weight: 600">{{ row.value }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="type" label="方向" width="70">
                <template #default="{ row }">
                  <el-tag :type="row.type === 'high' ? 'danger' : 'primary'" size="small">
                    {{ row.type === 'high' ? '偏高' : '偏低' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="severity" label="严重度">
                <template #default="{ row }">
                  <el-tag :type="row.severity === 'severe' ? 'danger' : row.severity === 'moderate' ? 'warning' : 'info'" size="small">
                    {{ { severe: '严重', moderate: '中度', mild: '轻度' }[row.severity] }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            <el-empty v-else description="暂无异常数据" :image-size="60" />
          </div>
          <el-empty v-else description="数据加载中..." :image-size="60" />
        </el-card>
      </div>

      <!-- 7日天气预报 -->
      <el-card style="margin: 0 24px 12px" v-if="forecastData.length > 0">
        <template #header><span>未来 7 天天气</span></template>
        <div class="forecast-row">
          <div class="fc-card" v-for="f in forecastData" :key="f.date">
            <div class="fc-day">{{ f.weekday }}</div>
            <div class="fc-date">{{ f.dateShort }}</div>
            <Icon :icon="weatherIcon(f.weatherText || f.emoji)" width="28" class="fc-icon" />
            <div class="fc-text">{{ f.weatherText }}</div>
            <div class="fc-temp">
              <span class="temp-max">{{ f.tempMax }}°</span>
              <span class="temp-min">/ {{ f.tempMin }}°</span>
            </div>
            <div class="fc-extra"><Icon icon="mdi:water-outline" width="12" />{{ f.precipitation }}mm</div>
            <div class="fc-extra"><Icon icon="mdi:weather-windy" width="12" />{{ f.windSpeedMax }}m/s</div>
          </div>
        </div>
      </el-card>

      <!-- 历史统计摘要 -->
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
import { cityApi, weatherApi, realAqiApi } from '@/api/modules'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import TrendLine from '@/components/charts/TrendLine.vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import HealthAdvice from '@/components/HealthAdvice.vue'

const route = useRoute()
const router = useRouter()
const cityStore = useCityStore()
const aqStore = useAirQualityStore()

const loading = ref(false)
const days = ref(60)
const city = ref(null)
const stations = ref([])
const forecastData = ref([])
const realtimeAqi = ref(null)
const aqiForecast = ref([])

const latestCity = computed(() =>
  aqStore.latestData.find((d) => d.cityId === city.value?.id)
)

const pollutants = computed(() => {
  const c = latestCity.value
  if (!c) return {}
  return { pm25: c.pm25, pm10: c.pm10, so2: c.so2, no2: c.no2, co: c.co, o3: c.o3 }
})

const combinedTrend = computed(() => {
  const history = aqStore.historyRecords || []
  const pred = aqStore.predictionResult?.predictions || []
  if (history.length === 0 && pred.length === 0) {
    return { dates: [], actual: [], predicted: [], upper: [], lower: [] }
  }
  return {
    dates: [...history.map((r) => r.date), ...pred.map((p) => p.date)],
    actual: [...history.map((r) => r.aqi), ...pred.map(() => null)],
    ma: null,
    predicted: [...history.map(() => null), ...pred.map((p) => p.predicted)],
    upper: [...history.map(() => null), ...pred.map((p) => p.upper)],
    lower: [...history.map(() => null), ...pred.map((p) => p.lower)],
  }
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

const iqrBarStyle = computed(() => {
  const r = aqStore.anomalyResult
  if (!r) return { normal: {}, box: {} }
  const range = r.upper_bound - r.lower_bound
  const boxStart = ((r.q1 - r.lower_bound) / range) * 100
  const boxWidth = ((r.q3 - r.q1) / range) * 100
  return {
    normal: { width: '100%' },
    box: { left: boxStart + '%', width: boxWidth + '%' },
  }
})

const anomalyRatio = computed(() => {
  const r = aqStore.anomalyResult
  if (!r || !r.total_points) return 0
  return ((r.anomaly_count / r.total_points) * 100).toFixed(1)
})

const historyStats = computed(() => {
  const h = aqStore.historyRecords
  if (!h || h.length === 0) return null
  const aqiArr = h.map((r) => r.aqi).filter(Boolean)
  const pm25Arr = h.map((r) => r.pm25).filter(Boolean)
  const avg = (arr) => (arr.reduce((s, v) => s + v, 0) / arr.length).toFixed(1)
  const max = (arr) => Math.max(...arr)
  const min = (arr) => Math.min(...arr)
  const goodDays = aqiArr.filter((v) => v <= 100).length
  return [
    { label: 'AQI 均值', value: avg(aqiArr), color: 'var(--primary)' },
    { label: 'AQI 最高', value: max(aqiArr), color: 'var(--danger)' },
    { label: 'AQI 最低', value: min(aqiArr), color: 'var(--success)' },
    { label: 'PM2.5 均值', value: avg(pm25Arr), suffix: 'μg/m³' },
    { label: '空气好的天', value: goodDays, suffix: '天', color: 'var(--success)' },
    { label: '优良率', value: ((goodDays / aqiArr.length) * 100).toFixed(1), suffix: '%', color: 'var(--success)' },
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
    await Promise.all([
      aqStore.fetchLatest(),
      aqStore.fetchHistory(id, days.value),
      aqStore.fetchPrediction(id),
      aqStore.fetchAnomalyDetect(id),
    ])
    weatherApi.getForecast(id, 7).then(d => { forecastData.value = d.forecast || [] }).catch(() => {})
    realAqiApi.getRealtime(id).then(d => { realtimeAqi.value = d }).catch(() => {})
    realAqiApi.getForecast(id, 5).then(d => { aqiForecast.value = d.forecast || [] }).catch(() => {})
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

function onCityChange(cityId) {
  router.push(`/city/${cityId}`)
}

function aqiColor(aqi) {
  if (!aqi) return '#8a8a8a'
  if (aqi <= 50) return '#2d6a4f'
  if (aqi <= 100) return '#d4a373'
  if (aqi <= 150) return '#e07a5f'
  if (aqi <= 200) return '#c1121f'
  return '#780116'
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

watch(() => route.params.id, loadFullData)

onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  loadFullData()
})
</script>

<style scoped>
.city-detail {
  min-height: 100vh;
  background: var(--bg-page, #eae6e1);
  color: var(--text-primary, #2c2c2c);
  transition: background-color 0.4s var(--bounce), color 0.4s var(--bounce);
}
.page-title { font-size: 16px; font-weight: 700; }
.station-tag { margin-right: 6px; }

/* KPI 不对称: 大卡 + 小卡网格 */
.kpi-row {
  display: flex;
  gap: 16px;
  padding: 12px 24px;
  align-items: stretch;
}
.kpi-hero {
  flex: 0 0 180px;
  background: var(--bg-card, rgba(255,255,255,0.85));
  border-radius: 14px;
  padding: 16px 20px;
  border-left: 4px solid;
  box-shadow: var(--shadow);
  backdrop-filter: blur(8px);
}
.kpi-big {
  font-size: 48px;
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -2px;
}
.kpi-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 10px;
}
.kpi-card {
  background: var(--bg-card, rgba(255,255,255,0.85));
  border-radius: 12px;
  padding: 12px 14px;
  text-align: left;
  box-shadow: var(--shadow);
  backdrop-filter: blur(8px);
  transition: transform 0.3s var(--bounce);
}
.kpi-card:hover { transform: translateY(-2px); }
.kpi-num {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary, #2c2c2c);
}
.kpi-sub {
  font-size: 12px;
  color: var(--text-muted, #8a8a8a);
  margin-top: 4px;
}

/* 天气卡片 */
.weather-section { padding: 0 24px; margin-top: 12px; }
.weather-grid {
  display: flex;
  align-items: center;
  gap: 24px;
}
.weather-cell { text-align: center; flex: 1; }
.weather-cell.main-weather { flex: 1.3; display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--primary); }
.weather-cond { font-size: 16px; font-weight: 600; color: var(--text-primary, #2c2c2c); }
.w-num { font-size: 22px; font-weight: 700; color: var(--text-primary, #2c2c2c); }
.w-num small { font-size: 13px; font-weight: 400; color: var(--text-muted, #8a8a8a); }
.w-label { font-size: 12px; color: var(--text-muted, #8a8a8a); margin-top: 4px; }

/* 实时 AQI 卡片 */
.realtime-grid {
  display: flex;
  align-items: center;
  gap: 12px;
}
.rt-cell { text-align: center; flex: 1; }
.rt-hero {
  flex: 0 0 90px;
  border-left: 4px solid;
  padding-left: 12px;
  text-align: left;
}
.rt-aqi { font-size: 36px; font-weight: 800; line-height: 1.1; }
.rt-level { font-size: 13px; color: var(--text-secondary, #5a5a5a); }
.rt-val { font-size: 18px; font-weight: 700; color: var(--text-primary, #2c2c2c); }
.rt-lbl { font-size: 11px; color: var(--text-muted, #8a8a8a); margin-top: 2px; }

/* AQI 预报 */
.fc-aqi { font-size: 24px; font-weight: 800; margin: 4px 0; }

/* 图表不对称网格 */
.charts-grid {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 12px;
  padding: 12px 24px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* IQR 可视化 */
.iqr-visual { padding: 12px 0; }
.iqr-bar-track {
  position: relative;
  height: 28px;
  background: linear-gradient(90deg, #fce4e4, #e6f5f3, #fce4e4);
  border-radius: 14px;
  overflow: hidden;
}
.iqr-zone.iqr-box {
  position: absolute;
  top: 0;
  height: 100%;
  background: rgba(13, 148, 136, 0.3);
  border: 2px solid var(--primary);
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 6px;
}
.iqr-label {
  font-size: 10px;
  color: var(--text-primary, #2c2c2c);
  font-weight: 600;
}
.iqr-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary, #5a5a5a);
  margin-top: 8px;
  padding: 0 4px;
}

/* 天气预报卡片 */
.forecast-row { display: flex; gap: 10px; overflow-x: auto; padding: 4px 0; }
.fc-card {
  flex: 0 0 100px; text-align: center;
  background: var(--bg-page, #eae6e1); border-radius: 12px; padding: 12px 6px;
  transition: transform 0.3s var(--bounce);
}
.fc-card:hover { transform: translateY(-3px) rotate(-1deg); }
.fc-day { font-size: 12px; font-weight: 600; color: var(--text-primary, #2c2c2c); }
.fc-date { font-size: 10px; color: var(--text-muted, #8a8a8a); }
.fc-icon { color: var(--primary); margin: 4px 0; }
.fc-text { font-size: 11px; color: var(--text-secondary, #5a5a5a); }
.fc-temp { margin-top: 4px; }
.temp-max { font-size: 15px; font-weight: 700; color: var(--text-primary, #2c2c2c); }
.temp-min { font-size: 12px; color: var(--text-muted, #8a8a8a); }
.fc-extra { font-size: 10px; color: var(--text-muted, #8a8a8a); display: flex; align-items: center; justify-content: center; gap: 2px; }
</style>
