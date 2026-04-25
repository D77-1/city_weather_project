<template>
  <div class="city-detail page-shell">
    <AppHeader @city-change="onCityChange" />

    <div class="detail-content" v-loading="loading">
      <section class="detail-hero panel-surface">
        <el-page-header @back="$router.push('/')" class="detail-header">
          <template #content>
            <span class="page-title">{{ city?.name }} 空气质量详情</span>
          </template>
        </el-page-header>

        <div class="hero-research-grid">
          <div>
            <span class="panel-kicker">Urban Research Page</span>
            <h2 class="hero-title">{{ city?.name || '城市' }}空气质量研究视图</h2>
            <p class="hero-summary">整合当前污染水平、天气背景、历史趋势、预测结果与异常信号，辅助分析单个城市在观测周期内的空气质量变化特征。</p>
          </div>
          <div class="hero-meta-card">
            <span class="meta-label">城市等级</span>
            <strong>{{ city?.cityLevel || '--' }}</strong>
            <span class="meta-label">监测站点</span>
            <strong>{{ stations.length }}</strong>
          </div>
        </div>
      </section>

      <div class="kpi-row" v-if="latestCity">
        <div class="kpi-hero panel-surface" :style="{ borderLeftColor: aqiColor(latestCity.aqi) }">
          <span class="panel-kicker">Current AQI</span>
          <div class="kpi-big" :style="{ color: aqiColor(latestCity.aqi) }">{{ latestCity.aqi }}</div>
          <div class="kpi-sub">AQI · {{ latestCity.qualityLevel }}</div>
        </div>
        <div class="kpi-grid">
          <div class="kpi-card panel-surface"><div class="kpi-num">{{ latestCity.pm25 }}</div><div class="kpi-sub">PM2.5</div></div>
          <div class="kpi-card panel-surface"><div class="kpi-num">{{ latestCity.pm10 }}</div><div class="kpi-sub">PM10</div></div>
          <div class="kpi-card panel-surface"><div class="kpi-num">{{ latestCity.so2 }}</div><div class="kpi-sub">SO₂</div></div>
          <div class="kpi-card panel-surface"><div class="kpi-num">{{ latestCity.no2 }}</div><div class="kpi-sub">NO₂</div></div>
          <div class="kpi-card panel-surface"><div class="kpi-num">{{ latestCity.co }}</div><div class="kpi-sub">CO</div></div>
          <div class="kpi-card panel-surface"><div class="kpi-num">{{ latestCity.o3 }}</div><div class="kpi-sub">O₃</div></div>
        </div>
      </div>

      <HealthAdvice v-if="latestCity" :aqi="latestCity.aqi" :quality-level="latestCity.qualityLevel" style="margin: 0 24px" />

      <div class="weather-section" v-if="latestCity && latestCity.temperature != null">
        <el-card class="weather-card panel-frame">
          <template #header>
            <div class="card-header">
              <div>
                <span class="panel-kicker">Meteorological Context</span>
                <h3>当前天气</h3>
              </div>
            </div>
          </template>
          <div class="weather-grid">
            <div class="weather-cell main-weather">
              <div class="weather-icon-wrap">
                <img :src="weatherIcon(latestCity.weatherCondition)" width="36" height="36" alt="" class="weather-svg" />
              </div>
              <span class="weather-cond">{{ latestCity.weatherCondition || '--' }}</span>
            </div>
            <div class="weather-cell"><div class="w-num">{{ latestCity.temperature }}<small>℃</small></div><div class="w-label">温度</div></div>
            <div class="weather-cell"><div class="w-num">{{ latestCity.humidity }}<small>%</small></div><div class="w-label">湿度</div></div>
            <div class="weather-cell"><div class="w-num">{{ latestCity.windSpeed }}<small>m/s</small></div><div class="w-label">{{ latestCity.windDirection }}风</div></div>
            <div class="weather-cell"><div class="w-num">{{ latestCity.rainfall }}<small>mm</small></div><div class="w-label">降水量</div></div>
          </div>
        </el-card>
      </div>

      <el-card class="realtime-card panel-frame" v-if="realtimeAqi" style="margin: 8px 24px">
        <template #header>
          <div class="card-header">
            <div>
              <span class="panel-kicker">Observed AQI</span>
              <h3>实时真实空气质量</h3>
            </div>
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
        <div v-if="realtimeAqi.primaryPollutant" class="realtime-note">
          首要污染物: <b style="color: var(--danger)">{{ realtimeAqi.primaryPollutant }}</b> · 数据按国标 HJ 633-2012 计算
        </div>
      </el-card>

      <el-card class="panel-frame" style="margin: 0 24px 8px" v-if="aqiForecast.length > 0">
        <template #header>
          <div class="card-header">
            <div>
              <span class="panel-kicker">Forecast Window</span>
              <h3>未来空气质量预报</h3>
            </div>
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

      <el-descriptions :column="5" border class="detail-descriptions" size="small">
        <el-descriptions-item label="省份">{{ city?.province }}</el-descriptions-item>
        <el-descriptions-item label="城市编码">{{ city?.cityCode }}</el-descriptions-item>
        <el-descriptions-item label="城市等级">{{ city?.cityLevel }}</el-descriptions-item>
        <el-descriptions-item label="常住人口">{{ city?.population != null ? city.population + ' 万' : '--' }}</el-descriptions-item>
        <el-descriptions-item label="监测站点">
          <el-tag v-for="s in stations" :key="s.id" size="small" class="station-tag">{{ s.stationName }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div class="charts-grid">
        <el-card class="panel-frame">
          <template #header>
            <div class="card-header">
              <div>
                <span class="panel-kicker">Trend Study</span>
                <h3>AQI 走势 + 预测</h3>
              </div>
              <el-radio-group v-model="days" size="small" @change="onDaysChange">
                <el-radio-button :value="30">30天</el-radio-button>
                <el-radio-button :value="60">60天</el-radio-button>
                <el-radio-button :value="90">90天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <TrendLine :trend-data="combinedTrend" :title="`${city?.name || ''} AQI 走势`" height="350px" />
        </el-card>

        <el-card class="panel-frame">
          <template #header>
            <div class="card-header">
              <div>
                <span class="panel-kicker">Pollutant Structure</span>
                <h3>污染物雷达分布</h3>
              </div>
            </div>
          </template>
          <RadarChart :pollutant-data="pollutants" :city-name="city?.name || ''" height="350px" />
        </el-card>
      </div>

      <div class="charts-grid charts-grid-secondary">
        <el-card class="panel-frame">
          <template #header>
            <div class="card-header">
              <div>
                <span class="panel-kicker">Compliance Review</span>
                <h3>达标了吗？</h3>
              </div>
            </div>
          </template>
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

        <el-card class="panel-frame">
          <template #header>
            <div class="card-header">
              <div>
                <span class="panel-kicker">Anomaly Research</span>
                <h3>最近异常记录</h3>
              </div>
            </div>
          </template>
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

      <el-card class="panel-frame" style="margin: 0 24px 12px" v-if="forecastData.length > 0">
        <template #header>
          <div class="card-header">
            <div>
              <span class="panel-kicker">Weather Outlook</span>
              <h3>未来 7 天天气</h3>
            </div>
          </div>
        </template>
        <div class="forecast-row">
          <div class="fc-card" v-for="f in forecastData" :key="f.date">
            <div class="fc-day">{{ f.weekday }}</div>
            <div class="fc-date">{{ f.dateShort }}</div>
            <img :src="weatherIcon(f.weatherText || f.emoji)" width="28" height="28" alt="" class="fc-icon" />
            <div class="fc-text">{{ f.weatherText }}</div>
            <div class="fc-temp"><span class="temp-max">{{ f.tempMax }}°</span><span class="temp-min">/ {{ f.tempMin }}°</span></div>
            <div class="fc-extra"><Icon icon="mdi:water-outline" width="12" />{{ f.precipitation }}mm</div>
            <div class="fc-extra"><Icon icon="mdi:weather-windy" width="12" />{{ f.windSpeedMax }}m/s</div>
          </div>
        </div>
      </el-card>

      <el-card class="panel-frame" style="margin: 0 24px 24px" v-if="historyStats">
        <template #header>
          <div class="card-header">
            <div>
              <span class="panel-kicker">Statistical Summary</span>
              <h3>历史统计（基于走势图区间）</h3>
            </div>
            <span class="stat-days-hint">当前范围：近 {{ days }} 天</span>
          </div>
        </template>
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
import { cityApi, airQualityApi, predictionApi, anomalyApi, weatherApi, realAqiApi } from '@/api/modules'
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
const routeRequestToken = ref(0)

function isDefinedNumber(value) {
  return value != null
}

function resetRouteDependentData() {
  city.value = null
  stations.value = []
  forecastData.value = []
  realtimeAqi.value = null
  aqiForecast.value = []
  aqStore.historyRecords = []
  aqStore.predictionResult = null
  aqStore.anomalyResult = null
}

const latestCity = computed(() =>
  aqStore.latestData.find((d) => d.cityId === city.value?.id)
)

const pollutants = computed(() => {
  const c = latestCity.value
  if (!c) return {}
  return { pm25: c.pm25, pm10: c.pm10, so2: c.so2, no2: c.no2, co: c.co, o3: c.o3 }
})

const combinedTrend = computed(() => {
  const rawHistory = aqStore.historyRecords || []
  const history = rawHistory.filter((r) => r.aqi != null)
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
  const aqiArr = h.map((r) => r.aqi).filter(isDefinedNumber)
  const pm25Arr = h.map((r) => r.pm25).filter(isDefinedNumber)
  if (aqiArr.length === 0 || pm25Arr.length === 0) return null
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
  if (!id) {
    routeRequestToken.value += 1
    resetRouteDependentData()
    return
  }
  const requestToken = ++routeRequestToken.value
  loading.value = true
  resetRouteDependentData()
  try {
    const detail = await cityApi.getDetail(id)
    if (requestToken !== routeRequestToken.value || id !== Number(route.params.id)) return
    city.value = detail
    stations.value = detail.stations || []
    cityStore.selectCity(id)

    const [latestData, historyRecords, predictionResult, anomalyResult] = await Promise.all([
      airQualityApi.getLatest(),
      airQualityApi.getHistory({ city_id: id, days: days.value }),
      predictionApi.run({ cityId: id, metric: 'aqi', window: 7, forecastDays: 7 }),
      anomalyApi.detect({ cityId: id, metric: 'aqi', days: 90 }),
    ])
    if (requestToken !== routeRequestToken.value || id !== Number(route.params.id)) return
    aqStore.latestData = latestData
    aqStore.historyRecords = historyRecords
    aqStore.predictionResult = predictionResult
    aqStore.anomalyResult = anomalyResult

    weatherApi.getForecast(id, 7)
      .then((data) => {
        if (requestToken === routeRequestToken.value && id === Number(route.params.id)) {
          forecastData.value = data.forecast || []
        }
      })
      .catch(() => {})
    realAqiApi.getRealtime(id)
      .then((data) => {
        if (requestToken === routeRequestToken.value && id === Number(route.params.id)) {
          realtimeAqi.value = data
        }
      })
      .catch(() => {})
    realAqiApi.getForecast(id, 5)
      .then((data) => {
        if (requestToken === routeRequestToken.value && id === Number(route.params.id)) {
          aqiForecast.value = data.forecast || []
        }
      })
      .catch(() => {})
  } finally {
    if (requestToken === routeRequestToken.value) {
      loading.value = false
    }
  }
}

async function onDaysChange() {
  const id = Number(route.params.id)
  if (!id) return
  const requestToken = routeRequestToken.value
  loading.value = true
  try {
    const historyRecords = await airQualityApi.getHistory({ city_id: id, days: days.value })
    if (requestToken === routeRequestToken.value && id === Number(route.params.id)) {
      aqStore.historyRecords = historyRecords
    }
  } finally {
    if (requestToken === routeRequestToken.value) {
      loading.value = false
    }
  }
}

function onCityChange(cityId) {
  router.push(`/city/${cityId}`)
}

function aqiColor(aqi) {
  if (aqi == null) return '#8a8a8a'
  if (aqi <= 50) return '#32d296'
  if (aqi <= 100) return '#f0b65a'
  if (aqi <= 150) return '#ff9e64'
  if (aqi <= 200) return '#ff6b81'
  return '#cf3c6d'
}

import clearSvg from '@/assets/weather/clear.svg'
import partlyCloudySvg from '@/assets/weather/partly-cloudy.svg'
import overcastSvg from '@/assets/weather/overcast.svg'
import fogSvg from '@/assets/weather/fog.svg'
import hazeSvg from '@/assets/weather/haze.svg'
import dustSvg from '@/assets/weather/dust.svg'
import drizzleSvg from '@/assets/weather/drizzle.svg'
import rainSvg from '@/assets/weather/rain.svg'
import heavyRainSvg from '@/assets/weather/heavy-rain.svg'
import thunderstormSvg from '@/assets/weather/thunderstorm.svg'
import snowSvg from '@/assets/weather/snow.svg'
import heavySnowSvg from '@/assets/weather/heavy-snow.svg'
import sleetSvg from '@/assets/weather/sleet.svg'

function weatherIcon(condition) {
  if (!condition) return overcastSvg
  const key = String(condition).trim()
  const map = {
    '晴': clearSvg,
    '晴间多云': partlyCloudySvg,
    '多云': partlyCloudySvg,
    '阴': overcastSvg,
    '雾': fogSvg,
    '薄雾': fogSvg,
    '霾': hazeSvg,
    '浮尘': dustSvg,
    '扬沙': dustSvg,
    '沙尘暴': dustSvg,
    '阵雨': rainSvg,
    '雷阵雨': thunderstormSvg,
    '毛毛雨': drizzleSvg,
    '小雨': drizzleSvg,
    '中雨': rainSvg,
    '大雨': heavyRainSvg,
    '暴雨': thunderstormSvg,
    '大暴雨': thunderstormSvg,
    '特大暴雨': thunderstormSvg,
    '冻雨': sleetSvg,
    '小雪': snowSvg,
    '中雪': snowSvg,
    '大雪': heavySnowSvg,
    '暴雪': heavySnowSvg,
    '阵雪': snowSvg,
    '雨夹雪': sleetSvg,
  }
  if (map[key]) return map[key]
  if (key.includes('雷')) return thunderstormSvg
  if (key.includes('暴雨')) return thunderstormSvg
  if (key.includes('大雨')) return heavyRainSvg
  if (key.includes('雨夹雪')) return sleetSvg
  if (key.includes('大雪') || key.includes('暴雪')) return heavySnowSvg
  if (key.includes('雪')) return snowSvg
  if (key.includes('雨')) return rainSvg
  if (key.includes('雾')) return fogSvg
  if (key.includes('霾')) return hazeSvg
  if (key.includes('尘') || key.includes('沙')) return dustSvg
  if (key.includes('多云') || key.includes('晴')) return partlyCloudySvg
  if (key.includes('阴')) return overcastSvg
  return overcastSvg
}

watch(() => route.params.id, () => {
  loadFullData()
})

onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  loadFullData()
})
</script>

<style scoped>
.city-detail {
  min-height: 100vh;
  background: transparent;
  color: var(--text-primary);
}

.page-shell {
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
  background: linear-gradient(135deg, rgba(127, 246, 234, 0.08), transparent 30%, transparent 72%, rgba(110, 168, 255, 0.08));
  pointer-events: none;
}

.panel-frame {
  position: relative;
  overflow: hidden;
}

.detail-content {
  position: relative;
}

.detail-hero {
  margin: 18px 24px 12px;
  padding: 18px 22px 24px;
  border-radius: 28px;
}

.detail-header {
  padding: 0;
}

.hero-research-grid {
  display: grid;
  grid-template-columns: 1.45fr 0.65fr;
  gap: 18px;
  margin-top: 18px;
}

.panel-kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--primary-light);
}

.panel-kicker::before {
  content: '';
  width: 18px;
  height: 1px;
  background: currentColor;
  opacity: 0.75;
}

.page-title {
  font-size: 18px;
  font-weight: 700;
}

.hero-title {
  margin-top: 18px;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.12;
}

.hero-summary {
  margin-top: 14px;
  line-height: 1.9;
  color: var(--text-secondary);
  max-width: 760px;
}

.hero-meta-card {
  align-self: start;
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid var(--border-color);
  background: rgba(8, 20, 34, 0.66);
}

.meta-label {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.hero-meta-card strong {
  font-size: 24px;
  color: var(--text-primary);
}

.station-tag {
  margin-right: 6px;
  margin-bottom: 6px;
}

.stat-days-hint {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}

.kpi-row {
  display: flex;
  gap: 16px;
  padding: 12px 24px;
  align-items: stretch;
}

.kpi-hero {
  flex: 0 0 220px;
  border-radius: 24px;
  padding: 20px 22px;
  border-left: 4px solid;
}

.kpi-big {
  margin-top: 16px;
  font-size: clamp(52px, 6vw, 70px);
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.05em;
}

.kpi-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.kpi-card {
  border-radius: 20px;
  padding: 16px 18px;
}

.kpi-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.kpi-sub {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.weather-section {
  padding: 0 24px;
  margin-top: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.card-header h3 {
  margin-top: 6px;
  font-size: 20px;
  color: var(--text-primary);
}

.weather-grid {
  display: grid;
  grid-template-columns: 1.2fr repeat(4, minmax(0, 1fr));
  gap: 16px;
  align-items: stretch;
}

.weather-cell {
  text-align: center;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 16px 12px;
  border-radius: 18px;
  background: rgba(7, 18, 31, 0.62);
  border: 1px solid rgba(124, 154, 188, 0.14);
}

.weather-cell.main-weather {
  gap: 8px;
  color: var(--primary-light);
}

.weather-icon-wrap {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  margin: 0 auto;
  border-radius: 18px;
  background: rgba(39, 211, 195, 0.08);
}

.weather-cond {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.w-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.w-num small {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-muted);
}

.w-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.realtime-grid {
  display: grid;
  grid-template-columns: 1.1fr repeat(6, minmax(0, 1fr));
  gap: 12px;
  align-items: center;
}

.rt-cell {
  text-align: center;
  padding: 12px 8px;
  border-radius: 18px;
  background: rgba(7, 18, 31, 0.52);
  border: 1px solid rgba(124, 154, 188, 0.14);
}

.rt-hero {
  border-left: 4px solid;
  padding-left: 14px;
  text-align: left;
  background: rgba(7, 18, 31, 0.72);
}

.rt-aqi {
  font-size: 42px;
  font-weight: 800;
  line-height: 1;
}

.rt-level {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.rt-val {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.rt-lbl {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.realtime-note {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-muted);
}

.fc-aqi {
  font-size: 28px;
  font-weight: 800;
  margin: 4px 0;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.85fr;
  gap: 12px;
  padding: 12px 24px;
}

.charts-grid-secondary {
  margin-top: 0;
}

.iqr-visual {
  padding: 12px 0;
}

.iqr-bar-track {
  position: relative;
  height: 30px;
  background: linear-gradient(90deg, rgba(255, 107, 129, 0.12), rgba(39, 211, 195, 0.16), rgba(110, 168, 255, 0.12));
  border-radius: 16px;
  overflow: hidden;
}

.iqr-zone.iqr-box {
  position: absolute;
  top: 0;
  height: 100%;
  background: rgba(39, 211, 195, 0.24);
  border: 2px solid var(--primary);
  border-radius: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 6px;
}

.iqr-label {
  font-size: 10px;
  color: var(--text-primary);
  font-weight: 600;
}

.iqr-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
  padding: 0 4px;
  flex-wrap: wrap;
}

.forecast-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 4px 0;
}

.fc-card {
  flex: 0 0 112px;
  text-align: center;
  background: rgba(7, 18, 31, 0.62);
  border: 1px solid rgba(124, 154, 188, 0.14);
  border-radius: 18px;
  padding: 14px 10px;
  transition: transform 0.3s var(--bounce), border-color 0.3s ease;
}

.fc-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-strong);
}

.fc-day {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.fc-date {
  font-size: 10px;
  color: var(--text-muted);
}

.fc-icon {
  color: var(--primary-light);
  margin: 4px 0;
}

.fc-text {
  font-size: 11px;
  color: var(--text-secondary);
}

.fc-temp {
  margin-top: 4px;
}

.temp-max {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.temp-min {
  font-size: 12px;
  color: var(--text-muted);
}

.fc-extra {
  font-size: 10px;
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.detail-descriptions {
  margin: 12px 24px;
}

@media (max-width: 1180px) {
  .hero-research-grid,
  .charts-grid,
  .weather-grid,
  .realtime-grid {
    grid-template-columns: 1fr;
  }

  .kpi-row {
    flex-direction: column;
  }

  .kpi-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .detail-hero,
  .weather-section,
  .charts-grid,
  .detail-descriptions {
    margin-left: 14px;
    margin-right: 14px;
    padding-left: 0;
    padding-right: 0;
  }

  .detail-hero {
    padding: 18px;
  }

  .kpi-row,
  .charts-grid {
    padding-left: 14px;
    padding-right: 14px;
  }

  .kpi-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
