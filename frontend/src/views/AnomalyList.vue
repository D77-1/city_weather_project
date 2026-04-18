<template>
  <div class="anomaly-page page-shell">
    <AppHeader />

    <div class="page-content">
      <section class="page-hero panel-surface">
        <el-page-header @back="goHome" content="异常数据检测" class="hero-header" />
        <div class="hero-grid">
          <div>
            <span class="panel-kicker">Monitoring Center</span>
            <h2 class="hero-title">异常事件监测中心</h2>
            <p class="hero-desc">集中查看异常记录、等级分布与处理状态，支持按城市、指标、严重度进行筛选，并直接执行检测与状态处置。</p>
          </div>
          <div class="hero-side-note">
            <span class="side-label">当前记录数</span>
            <strong>{{ aqStore.anomalyList.length }}</strong>
            <span class="side-caption">前端基于当前列表实时汇总</span>
          </div>
        </div>
      </section>

      <div class="summary-grid">
        <div class="summary-card panel-surface">
          <span class="summary-label">待处理</span>
          <strong class="summary-value">{{ anomalySummary.pending }}</strong>
          <span class="summary-foot">需确认或忽略</span>
        </div>
        <div class="summary-card panel-surface">
          <span class="summary-label">高风险事件</span>
          <strong class="summary-value danger">{{ anomalySummary.severe }}</strong>
          <span class="summary-foot">严重等级异常</span>
        </div>
        <div class="summary-card panel-surface">
          <span class="summary-label">已确认</span>
          <strong class="summary-value success">{{ anomalySummary.confirmed }}</strong>
          <span class="summary-foot">已纳入处置记录</span>
        </div>
        <div class="summary-card panel-surface">
          <span class="summary-label">涉及城市</span>
          <strong class="summary-value accent">{{ anomalySummary.cityCount }}</strong>
          <span class="summary-foot">当前筛选结果覆盖</span>
        </div>
      </div>

      <section class="filter-panel panel-surface">
        <div class="filter-head">
          <div>
            <span class="panel-kicker">Filter Console</span>
            <h3>筛选与检测控制</h3>
          </div>
        </div>
        <div class="filter-bar">
          <el-select v-model="filters.city_id" placeholder="全部城市" clearable style="width: 170px" @change="loadList">
            <el-option v-for="c in cityStore.cities" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-select v-model="filters.metric" placeholder="全部指标" clearable style="width: 140px" @change="loadList">
            <el-option label="AQI" value="aqi" />
            <el-option label="PM2.5" value="pm25" />
            <el-option label="PM10" value="pm10" />
          </el-select>
          <el-select v-model="filters.severity" placeholder="全部等级" clearable style="width: 140px" @change="loadList">
            <el-option label="轻度" value="mild" />
            <el-option label="中度" value="moderate" />
            <el-option label="重度" value="severe" />
          </el-select>
          <el-button type="primary" class="detect-btn" @click="runDetectAll">执行异常检测</el-button>
        </div>
      </section>

      <section class="table-panel panel-surface">
        <div class="table-head">
          <div>
            <span class="panel-kicker">Anomaly Ledger</span>
            <h3>异常事件列表</h3>
          </div>
        </div>
        <el-table :data="aqStore.anomalyList" stripe border style="margin-top: 12px" v-loading="loading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="城市" width="90">
            <template #default="{ row }">{{ getCityName(row.cityId) }}</template>
          </el-table-column>
          <el-table-column prop="metricName" label="指标" width="90">
            <template #default="{ row }">{{ formatMetricName(row.metricName) }}</template>
          </el-table-column>
          <el-table-column prop="actualValue" label="实际值" width="90" />
          <el-table-column label="正常范围" width="150">
            <template #default="{ row }">{{ row.lowerBound }} ~ {{ row.upperBound }}</template>
          </el-table-column>
          <el-table-column prop="anomalyType" label="方向" width="80">
            <template #default="{ row }">
              <el-tag :type="row.anomalyType === 'high' ? 'danger' : 'primary'" size="small">{{ row.anomalyType === 'high' ? '偏高' : '偏低' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重度" width="90">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)" size="small">{{ { severe: '严重', moderate: '中度', mild: '轻度' }[row.severity] || row.severity }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="recordTime" label="时间" width="130">
            <template #default="{ row }">{{ formatRecordDate(row.recordTime) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'confirmed' ? 'success' : row.status === 'dismissed' ? 'info' : 'warning'" size="small">
                {{ { confirmed: '已确认', dismissed: '已忽略', pending: '待处理' }[row.status] || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === 'pending'" type="success" size="small" @click="updateStatus(row.id, 'confirmed')">确认</el-button>
              <el-button v-if="row.status === 'pending'" type="info" size="small" @click="updateStatus(row.id, 'dismissed')">忽略</el-button>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCityStore } from '@/stores/city'
import { useAirQualityStore } from '@/stores/airQuality'
import { anomalyApi } from '@/api/modules'
import AppHeader from '@/components/layout/AppHeader.vue'

const router = useRouter()
const cityStore = useCityStore()
const aqStore = useAirQualityStore()
const loading = ref(false)

function goHome() {
  router.push('/')
}

const filters = reactive({ city_id: null, metric: null, severity: null })

const anomalySummary = computed(() => {
  const list = aqStore.anomalyList || []
  return {
    pending: list.filter(item => item.status === 'pending').length,
    severe: list.filter(item => item.severity === 'severe').length,
    confirmed: list.filter(item => item.status === 'confirmed').length,
    cityCount: new Set(list.map(item => item.cityId)).size,
  }
})

async function loadList() {
  loading.value = true
  try {
    const params = { limit: 100 }
    if (filters.city_id) params.city_id = filters.city_id
    if (filters.metric) params.metric = filters.metric
    if (filters.severity) params.severity = filters.severity
    await aqStore.fetchAnomalyList(params)
  } finally {
    loading.value = false
  }
}

async function runDetectAll() {
  loading.value = true
  try {
    const targetCities = filters.city_id
      ? [{ id: filters.city_id }]
      : cityStore.cities
    for (const city of targetCities) {
      await anomalyApi.detect({ cityId: city.id, metric: filters.metric || 'aqi', days: 90 })
    }
    await loadList()
  } finally {
    loading.value = false
  }
}

async function updateStatus(eventId, status) {
  await anomalyApi.updateStatus(eventId, { status })
  await loadList()
}

function getCityName(cityId) {
  return cityStore.cities.find((c) => c.id === cityId)?.name || cityId
}

function formatMetricName(metricName) {
  return typeof metricName === 'string' ? metricName.toUpperCase() : '--'
}

function formatRecordDate(recordTime) {
  return typeof recordTime === 'string' ? recordTime.slice(0, 10) : '--'
}

function severityType(s) {
  if (s === 'severe') return 'danger'
  if (s === 'moderate') return 'warning'
  return 'info'
}

onMounted(async () => {
  if (cityStore.cities.length === 0) await cityStore.fetchCities()
  await loadList()
})
</script>

<style scoped>
.anomaly-page {
  min-height: 100vh;
  background: transparent;
  color: var(--text-primary);
}

.page-shell {
  padding-bottom: 24px;
}

.page-content {
  padding: 18px 24px 0;
}

.panel-surface {
  position: relative;
  overflow: hidden;
  border-radius: 26px;
  border: 1px solid var(--border-color);
  background: linear-gradient(180deg, rgba(10, 22, 37, 0.86), rgba(8, 18, 31, 0.72));
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
}

.panel-surface::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(135deg, rgba(127, 246, 234, 0.08), transparent 30%, transparent 70%, rgba(110, 168, 255, 0.08));
  pointer-events: none;
}

.page-hero,
.filter-panel,
.table-panel {
  padding: 20px 22px;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.5fr 0.6fr;
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

.hero-title {
  margin-top: 18px;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.1;
}

.hero-desc {
  margin-top: 12px;
  max-width: 760px;
  line-height: 1.85;
  color: var(--text-secondary);
}

.hero-side-note {
  align-self: start;
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(124, 154, 188, 0.16);
  background: rgba(7, 18, 31, 0.62);
}

.side-label,
.summary-label {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--text-muted);
  text-transform: uppercase;
}

.hero-side-note strong {
  font-size: 32px;
}

.side-caption,
.summary-foot {
  font-size: 12px;
  color: var(--text-secondary);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.summary-card {
  padding: 18px 20px;
}

.summary-value {
  display: block;
  margin: 12px 0 6px;
  font-size: clamp(28px, 5vw, 40px);
  line-height: 1;
  font-weight: 800;
  color: var(--text-primary);
}

.summary-value.danger {
  color: var(--danger);
}

.summary-value.success {
  color: var(--success);
}

.summary-value.accent {
  color: var(--accent-light);
}

.filter-panel,
.table-panel {
  margin-top: 14px;
}

.filter-head h3,
.table-head h3 {
  margin-top: 8px;
  font-size: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.detect-btn {
  min-width: 140px;
  box-shadow: 0 16px 28px rgba(39, 211, 195, 0.16);
}

@media (max-width: 1100px) {
  .hero-grid,
  .summary-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 768px) {
  .page-content {
    padding: 14px 14px 0;
  }

  .hero-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .page-hero,
  .filter-panel,
  .table-panel {
    padding: 18px;
  }
}
</style>
