<template>
  <div class="report-page page-shell">
    <AppHeader @city-change="onCityChange" />

    <div class="report-content" v-loading="loading">
      <section class="page-section report-intro">
        <div class="section-heading">
          <span class="section-kicker">REPORT</span>
          <h2 class="section-title">{{ cityName }} 数据报告</h2>
        </div>

        <el-card class="intro-card">
          <div class="intro-topbar">
            <div>
              <p class="intro-kicker">研究周期</p>
              <h3 class="intro-title">围绕空气质量分布、结构、天气与月均变化生成汇总报告</h3>
            </div>
            <el-radio-group v-model="period" @change="loadReport">
              <el-radio-button value="30">近30天</el-radio-button>
              <el-radio-button value="90">近90天</el-radio-button>
              <el-radio-button value="180">半年</el-radio-button>
              <el-radio-button value="365">近一年</el-radio-button>
            </el-radio-group>
          </div>
        </el-card>
      </section>

      <section class="page-section" v-if="stats">
        <div class="section-heading compact-heading">
          <span class="section-kicker">OVERVIEW</span>
          <h2 class="section-title">报告总览</h2>
        </div>
        <div class="stat-row">
          <el-card class="stat-card stat-big">
            <div class="stat-val" style="color: var(--aq-primary)">{{ stats.avg }}</div>
            <div class="stat-label">平均 AQI</div>
          </el-card>
          <el-card class="stat-card stat-mid">
            <div class="stat-val" style="color: var(--aq-danger)">{{ stats.max }}</div>
            <div class="stat-label">峰值 AQI</div>
          </el-card>
          <el-card class="stat-card stat-mid">
            <div class="stat-val" style="color: var(--aq-success)">{{ stats.min }}</div>
            <div class="stat-label">谷值 AQI</div>
          </el-card>
        </div>
        <div class="stat-row stat-row-2">
          <el-card class="stat-card stat-mid">
            <div class="stat-val" style="color: var(--aq-success)">{{ stats.good }} 天</div>
            <div class="stat-label">优良天数</div>
          </el-card>
          <el-card class="stat-card stat-big">
            <div class="stat-val" style="color: var(--aq-primary)">{{ stats.goodRate }}%</div>
            <div class="stat-label">优良率</div>
          </el-card>
          <el-card class="stat-card stat-sm">
            <div class="stat-val" style="color: var(--aq-warning)">{{ stats.pollutedDays }} 天</div>
            <div class="stat-label">污染天数</div>
          </el-card>
        </div>
      </section>

      <section class="page-section report-grid">
        <div>
          <div class="section-heading compact-heading">
            <span class="section-kicker">DISTRIBUTION</span>
            <h2 class="section-title">分布与等级</h2>
          </div>
          <div class="charts-row">
            <el-card class="report-card">
              <template #header><div class="card-header"><span>AQI 分布区间</span><p>统计不同空气质量区间的出现天数。</p></div></template>
              <EChartWrapper :option="histogramOption" height="300px" />
            </el-card>
            <el-card class="report-card">
              <template #header><div class="card-header"><span>空气质量等级占比</span><p>从比例视角展示优良与污染等级构成。</p></div></template>
              <EChartWrapper :option="pieOption" height="300px" />
            </el-card>
          </div>
        </div>

        <div>
          <div class="section-heading compact-heading">
            <span class="section-kicker">TRENDS</span>
            <h2 class="section-title">月均与相关性</h2>
          </div>
          <div class="charts-row">
            <el-card class="report-card">
              <template #header><div class="card-header"><span>每月 AQI 均值</span><p>适合展示阶段性空气质量改善或恶化趋势。</p></div></template>
              <EChartWrapper :option="monthlyOption" height="300px" />
            </el-card>
            <el-card class="report-card">
              <template #header><div class="card-header"><span>各污染物月均浓度</span><p>比较 PM2.5、PM10、NO₂、O₃ 的月均变化。</p></div></template>
              <EChartWrapper :option="pollutantMonthlyOption" height="300px" />
            </el-card>
          </div>
        </div>
      </section>

      <section class="page-section">
        <div class="section-heading compact-heading">
          <span class="section-kicker">CORRELATION</span>
          <h2 class="section-title">深度分析</h2>
        </div>
        <div class="charts-row">
          <el-card class="report-card">
            <template #header><div class="card-header"><span>污染物相关性矩阵</span><p>展示六项污染物浓度之间的皮尔逊相关系数，揭示同源性。</p></div></template>
            <EChartWrapper :option="heatmapOption" height="360px" />
          </el-card>
          <el-card class="report-card">
            <template #header><div class="card-header"><span>季度 AQI 分布</span><p>通过箱线图展示不同季度的 AQI 分布特征与季节差异。</p></div></template>
            <EChartWrapper :option="boxplotOption" height="360px" />
          </el-card>
        </div>
      </section>

      <section class="page-section" v-if="forecast.length > 0">
        <div class="section-heading compact-heading">
          <span class="section-kicker">FORECAST</span>
          <h2 class="section-title">未来 7 天天气</h2>
        </div>
        <el-card class="report-card forecast-card-wrap">
          <div class="forecast-row">
            <div class="fc-card" v-for="f in forecast" :key="f.date">
              <div class="fc-day">{{ f.weekday }}</div>
              <div class="fc-date">{{ f.dateShort }}</div>
              <Icon :icon="weatherIcon(f.weatherText || f.emoji)" width="32" class="fc-icon" />
              <div class="fc-text">{{ f.weatherText }}</div>
              <div class="fc-temp">
                <span class="temp-max">{{ f.tempMax }}°</span>
                <span class="temp-min">{{ f.tempMin }}°</span>
              </div>
              <div class="fc-detail">
                <span><Icon icon="mdi:water-outline" width="12" /> {{ f.precipitation }}mm</span>
                <span><Icon icon="mdi:weather-windy" width="12" /> {{ f.windSpeedMax }}m/s</span>
              </div>
            </div>
          </div>
        </el-card>
      </section>

      <section class="page-section">
        <div class="section-heading compact-heading">
          <span class="section-kicker">DETAILS</span>
          <h2 class="section-title">历史数据明细</h2>
        </div>
        <el-card class="report-card">
          <template #header>
            <div class="table-header">
              <div>
                <span>历史数据明细</span>
                <p>展示最近一段时间的原始监测结果。</p>
              </div>
              <el-button size="small" @click="exportCSV">导出 CSV</el-button>
            </div>
          </template>
          <el-table :data="history" stripe size="small" max-height="400">
            <el-table-column prop="date" label="日期" width="100" />
            <el-table-column prop="aqi" label="AQI" width="70" />
            <el-table-column prop="pm25" label="PM2.5" width="80" />
            <el-table-column prop="pm10" label="PM10" width="80" />
            <el-table-column prop="so2" label="SO₂" width="70" />
            <el-table-column prop="no2" label="NO₂" width="70" />
            <el-table-column prop="co" label="CO" width="70" />
            <el-table-column prop="o3" label="O₃" width="70" />
            <el-table-column prop="temperature" label="温度℃" width="80" />
            <el-table-column prop="humidity" label="湿度%" width="80" />
          </el-table>
        </el-card>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCityStore } from '@/stores/city'
import { airQualityApi, weatherApi } from '@/api/modules'
import { Icon } from '@iconify/vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import EChartWrapper from '@/components/charts/EChartWrapper.vue'

const cityStore = useCityStore()
const loading = ref(false)
const period = ref('90')
const history = ref([])
const forecast = ref([])

const cityName = computed(() => cityStore.currentCity?.name || '全国')

const stats = computed(() => {
  if (history.value.length === 0) return null
  const aqis = history.value.map(r => r.aqi).filter(Boolean)
  const avg = arr => (arr.reduce((s, v) => s + v, 0) / arr.length)
  const good = aqis.filter(v => v <= 100).length
  return {
    avg: avg(aqis).toFixed(0),
    max: Math.max(...aqis),
    min: Math.min(...aqis),
    good,
    goodRate: ((good / aqis.length) * 100).toFixed(1),
    totalDays: aqis.length,
    pollutedDays: aqis.filter(v => v > 100).length,
  }
})

const histogramOption = computed(() => {
  const bins = [0, 50, 100, 150, 200, 300, 500]
  const labels = ['优(0-50)', '良(51-100)', '轻度(101-150)', '中度(151-200)', '重度(201-300)', '严重(>300)']
  const colors = ['#2d6a4f', '#a8743f', '#c86b4b', '#b42318', '#780116', '#4a0010']
  const counts = new Array(6).fill(0)
  history.value.forEach(r => {
    if (!r.aqi) return
    for (let i = 0; i < bins.length - 1; i++) {
      if (r.aqi >= bins[i] && r.aqi <= bins[i + 1]) { counts[i]++; break }
    }
  })
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 24, bottom: 40 },
    xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, color: '#9bb0c8' } },
    yAxis: { type: 'value', name: '天数', nameTextStyle: { color: '#9bb0c8' }, splitLine: { lineStyle: { color: 'rgba(124,154,188,0.12)' } } },
    series: [{ type: 'bar', data: counts.map((v, i) => ({ value: v, itemStyle: { color: colors[i], borderRadius: [10, 10, 0, 0] } })), barWidth: '60%' }],
  }
})

const pieOption = computed(() => {
  const levels = ['优', '良', '轻度污染', '中度污染', '重度污染', '严重污染']
  const colors = ['#2d6a4f', '#a8743f', '#c86b4b', '#b42318', '#780116', '#4a0010']
  const bins = [0, 50, 100, 150, 200, 300, 500]
  const counts = new Array(6).fill(0)
  history.value.forEach(r => {
    if (!r.aqi) return
    for (let i = 0; i < bins.length - 1; i++) {
      if (r.aqi >= bins[i] && r.aqi <= bins[i + 1]) { counts[i]++; break }
    }
  })
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}天 ({d}%)' },
    series: [{
      type: 'pie', radius: ['42%', '72%'],
      data: levels.map((n, i) => ({ name: n, value: counts[i], itemStyle: { color: colors[i] } })).filter(d => d.value > 0),
      label: { formatter: '{b}\n{d}%', fontSize: 11, color: '#b7c8dc' },
    }],
  }
})

const monthlyOption = computed(() => {
  const monthMap = {}
  history.value.forEach(r => {
    const m = r.date?.slice(0, 7)
    if (!m) return
    if (!monthMap[m]) monthMap[m] = []
    monthMap[m].push(r.aqi)
  })
  const months = Object.keys(monthMap).sort()
  const avgs = months.map(m => Math.round(monthMap[m].reduce((s, v) => s + v, 0) / monthMap[m].length))
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 20, top: 24, bottom: 40 },
    xAxis: { type: 'category', data: months, axisLabel: { color: '#9bb0c8' } },
    yAxis: { type: 'value', name: 'AQI', nameTextStyle: { color: '#9bb0c8' }, splitLine: { lineStyle: { color: 'rgba(124,154,188,0.12)' } } },
    series: [{
      type: 'bar', data: avgs,
      itemStyle: { color: (p) => p.value > 100 ? '#ff6b81' : p.value > 50 ? '#f0b65a' : '#32d296', borderRadius: [10, 10, 0, 0] },
      label: { show: true, position: 'top', fontSize: 10, color: '#b7c8dc' },
    }],
  }
})

const pollutantMonthlyOption = computed(() => {
  const monthMap = {}
  history.value.forEach(r => {
    const m = r.date?.slice(0, 7)
    if (!m) return
    if (!monthMap[m]) monthMap[m] = { pm25: [], pm10: [], no2: [], o3: [] }
    monthMap[m].pm25.push(r.pm25 || 0)
    monthMap[m].pm10.push(r.pm10 || 0)
    monthMap[m].no2.push(r.no2 || 0)
    monthMap[m].o3.push(r.o3 || 0)
  })
  const months = Object.keys(monthMap).sort()
  const avg = arr => arr.length ? Math.round(arr.reduce((s, v) => s + v, 0) / arr.length * 10) / 10 : 0
  const items = [
    { name: 'PM2.5', key: 'pm25', color: '#1e5c5a' },
    { name: 'PM10', key: 'pm10', color: '#5f6f52' },
    { name: 'NO₂', key: 'no2', color: '#a8743f' },
    { name: 'O₃', key: 'o3', color: '#c86b4b' },
  ]
  return {
    tooltip: { trigger: 'axis' },
    legend: { data: items.map(i => i.name), bottom: 5, textStyle: { color: '#b7c8dc' } },
    grid: { left: 50, right: 20, top: 24, bottom: 50 },
    xAxis: { type: 'category', data: months, axisLabel: { color: '#9bb0c8' } },
    yAxis: { type: 'value', name: 'μg/m³', nameTextStyle: { color: '#9bb0c8' }, splitLine: { lineStyle: { color: 'rgba(124,154,188,0.12)' } } },
    series: items.map(item => ({
      name: item.name, type: 'line', smooth: true, symbol: 'none',
      data: months.map(m => avg(monthMap[m][item.key])),
      lineStyle: { color: item.color, width: 2.5 }, itemStyle: { color: item.color },
    })),
  }
})

// 污染物相关性热力图
const heatmapOption = computed(() => {
  const metrics = ['PM2.5', 'PM10', 'SO₂', 'NO₂', 'CO', 'O₃']
  const keys = ['pm25', 'pm10', 'so2', 'no2', 'co', 'o3']
  const rows = history.value.filter(r => r.aqi)

  if (rows.length < 5) return { graphic: { type: 'text', left: 'center', top: 'middle', style: { text: '数据不足', fill: '#999' } } }

  // 提取各指标数组
  const arrays = keys.map(k => rows.map(r => r[k] || 0))

  // 计算皮尔逊相关系数
  function pearson(a, b) {
    const n = a.length
    const meanA = a.reduce((s, v) => s + v, 0) / n
    const meanB = b.reduce((s, v) => s + v, 0) / n
    let num = 0, denA = 0, denB = 0
    for (let i = 0; i < n; i++) {
      const da = a[i] - meanA, db = b[i] - meanB
      num += da * db; denA += da * da; denB += db * db
    }
    const den = Math.sqrt(denA * denB)
    return den === 0 ? 0 : num / den
  }

  const data = []
  for (let i = 0; i < keys.length; i++) {
    for (let j = 0; j < keys.length; j++) {
      const r = parseFloat(pearson(arrays[i], arrays[j]).toFixed(2))
      data.push([j, i, r])
    }
  }

  return {
    tooltip: { formatter: p => `${metrics[p.value[1]]} vs ${metrics[p.value[0]]}<br/>相关系数: ${p.value[2]}` },
    grid: { left: 70, right: 40, top: 10, bottom: 50 },
    xAxis: { type: 'category', data: metrics, axisLabel: { color: '#9bb0c8' }, splitArea: { show: true, areaStyle: { color: ['rgba(124,154,188,0.04)', 'rgba(124,154,188,0.08)'] } } },
    yAxis: { type: 'category', data: metrics, axisLabel: { color: '#9bb0c8' }, splitArea: { show: true, areaStyle: { color: ['rgba(124,154,188,0.04)', 'rgba(124,154,188,0.08)'] } } },
    visualMap: { min: -1, max: 1, calculable: true, orient: 'vertical', right: 0, top: 'center', inRange: { color: ['#32d296', '#1a2e3d', '#ff6b81'] }, textStyle: { color: '#9bb0c8' } },
    series: [{
      type: 'heatmap', data,
      label: { show: true, formatter: p => p.value[2].toFixed(2), fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' } },
    }],
  }
})

// 季度 AQI 箱线图
const boxplotOption = computed(() => {
  const quarters = { 'Q1 春': [], 'Q2 夏': [], 'Q3 秋': [], 'Q4 冬': [] }
  history.value.forEach(r => {
    if (!r.aqi || !r.date) return
    const month = parseInt(r.date.slice(5, 7))
    if (month >= 3 && month <= 5) quarters['Q1 春'].push(r.aqi)
    else if (month >= 6 && month <= 8) quarters['Q2 夏'].push(r.aqi)
    else if (month >= 9 && month <= 11) quarters['Q3 秋'].push(r.aqi)
    else quarters['Q4 冬'].push(r.aqi)
  })

  const labels = Object.keys(quarters)
  const hasData = labels.some(k => quarters[k].length >= 3)
  if (!hasData) return { graphic: { type: 'text', left: 'center', top: 'middle', style: { text: '数据不足，建议选择更长周期', fill: '#999' } } }

  // 计算箱线图五数概括
  function calcBox(arr) {
    if (arr.length < 3) return [0, 0, 0, 0, 0]
    arr.sort((a, b) => a - b)
    const q1 = arr[Math.floor(arr.length * 0.25)]
    const median = arr[Math.floor(arr.length * 0.5)]
    const q3 = arr[Math.floor(arr.length * 0.75)]
    const iqr = q3 - q1
    const min = Math.max(arr[0], q1 - 1.5 * iqr)
    const max = Math.min(arr[arr.length - 1], q3 + 1.5 * iqr)
    return [min, q1, median, q3, max]
  }

  const boxData = labels.map(k => calcBox(quarters[k]))
  const sampleCounts = labels.map(k => quarters[k].length)
  const colors = ['#2d6a4f', '#a8743f', '#c86b4b', '#1e5c5a']

  return {
    tooltip: {
      trigger: 'item',
      formatter: function(p) {
        const idx = p.dataIndex
        const d = boxData[idx]
        const name = labels[idx]
        if (!d) return ''
        return `<b>${name}</b> (${sampleCounts[idx]}天)<br/>最大: ${d[4]}<br/>Q3: ${d[3]}<br/>中位数: ${d[2]}<br/>Q1: ${d[1]}<br/>最小: ${d[0]}`
      },
    },
    grid: { left: 55, right: 20, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: labels, axisLabel: { color: '#9bb0c8', fontWeight: 'bold' } },
    yAxis: { type: 'value', name: 'AQI', nameTextStyle: { color: '#9bb0c8' }, splitLine: { lineStyle: { color: 'rgba(124,154,188,0.12)' } } },
    series: [{
      type: 'boxplot',
      data: boxData.map((d, i) => ({ value: d, itemStyle: { color: 'rgba(30,92,90,0.12)', borderColor: colors[i], borderWidth: 2 } })),
    }],
  }
})

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

function escapeCSVCell(value, forceText = false) {
  const text = value == null ? '' : String(value)
  const normalized = forceText ? `="${text.replace(/"/g, '""')}"` : text
  if (/[",\n\r]/.test(normalized)) return `"${normalized.replace(/"/g, '""')}"`
  return normalized
}

function exportCSV() {
  const headers = ['日期', 'AQI', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', '温度', '湿度']
  const rows = history.value.map(r => [
    escapeCSVCell(r.date, true),
    escapeCSVCell(r.aqi),
    escapeCSVCell(r.pm25),
    escapeCSVCell(r.pm10),
    escapeCSVCell(r.so2),
    escapeCSVCell(r.no2),
    escapeCSVCell(r.co),
    escapeCSVCell(r.o3),
    escapeCSVCell(r.temperature),
    escapeCSVCell(r.humidity),
  ])
  const csv = '\uFEFF' + [headers, ...rows].map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${cityName.value}_air_quality_report.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

async function loadReport() {
  const id = cityStore.currentCityId
  if (!id) return
  loading.value = true
  try {
    const days = Number(period.value)
    const [hist, fc, wh] = await Promise.all([
      airQualityApi.getHistory({ city_id: id, days }),
      weatherApi.getForecast(id, 7),
      weatherApi.getHistory(id, Math.min(days, 90)),
    ])
    // 将天气历史按日期合并到空气质量数据（补充温度湿度）
    const weatherMap = {}
    for (const w of (wh.history || wh || [])) {
      if (w.date) weatherMap[w.date] = w
    }
    history.value = (hist || []).map(r => {
      const w = weatherMap[r.date]
      return {
        ...r,
        temperature: r.temperature ?? (w ? w.tempMean : null),
        humidity: r.humidity ?? (w ? w.humidity : null),
      }
    })
    forecast.value = fc.forecast || []
  } finally {
    loading.value = false
  }
}

function onCityChange(cityId) {
  cityStore.selectCity(cityId)
  loadReport()
}

onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  if (!cityStore.currentCityId && cityStore.cities.length > 0) cityStore.selectCity(cityStore.cities[0].id)
  loadReport()
})
</script>

<style scoped>
.report-page {
  padding-bottom: 28px;
}

/* 卡片使用全局暗色主题，不再单独覆盖 */

.intro-topbar,
.card-header,
.table-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.intro-kicker {
  font-family: var(--aq-mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--aq-accent);
}

.intro-title {
  margin-top: 10px;
  font-family: var(--aq-display);
  font-size: 32px;
  line-height: 1.14;
  color: var(--aq-ink);
}

.stat-row {
  display: flex;
  gap: 12px;
}

.stat-row-2 {
  margin-top: 12px;
}

.stat-card {
  text-align: left;
}

.stat-big {
  flex: 1.4;
}

.stat-mid {
  flex: 1;
}

.stat-sm {
  flex: 0.7;
}

.stat-val {
  font-family: var(--aq-display);
  font-size: 42px;
  font-weight: 700;
}

.stat-label,
.card-header p,
.table-header p,
.fc-text,
.fc-detail,
.fc-date,
.temp-min {
  color: var(--aq-ink-soft);
}

.report-grid {
  display: grid;
  gap: 18px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
}

.forecast-row {
  display: flex;
  justify-content: space-around;
}

.fc-card {
  flex: 0 0 132px;
  text-align: center;
  background: linear-gradient(180deg, rgba(39, 211, 195, 0.06), rgba(110, 168, 255, 0.05));
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 16px 10px;
}

.fc-day {
  font-weight: 700;
  color: var(--aq-ink);
}

.fc-icon {
  color: var(--aq-primary);
  margin: 6px 0;
}

.fc-temp {
  margin-top: 6px;
}

.temp-max {
  font-size: 18px;
  font-weight: 700;
  color: var(--aq-ink);
}

.table-header span,
.card-header span {
  color: var(--aq-ink);
  font-weight: 700;
}

@media (max-width: 1200px) {
  .intro-topbar,
  .stat-row,
  .charts-row {
    flex-direction: column;
    grid-template-columns: 1fr;
  }
}
</style>
