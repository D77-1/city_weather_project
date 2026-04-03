<template>
  <div class="anomaly-page page-shell">
    <AppHeader />

    <section class="page-section anomaly-intro">
      <div class="section-heading">
        <span class="section-kicker">ANOMALY</span>
        <h2 class="section-title">异常数据检测</h2>
      </div>

      <el-card class="filter-card">
        <div class="filter-topbar">
          <div>
            <p class="filter-kicker">筛选与处理</p>
            <h3 class="filter-title">统一查看城市异常事件，并支持批量重跑检测</h3>
          </div>
          <el-button type="primary" @click="runDetectAll">执行异常检测</el-button>
        </div>

        <div class="filter-bar">
          <el-select v-model="filters.city_id" placeholder="全部城市" clearable style="width: 160px" @change="loadList">
            <el-option v-for="c in cityStore.cities" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
          <el-select v-model="filters.metric" placeholder="全部指标" clearable style="width: 130px" @change="loadList">
            <el-option label="AQI" value="aqi" />
            <el-option label="PM2.5" value="pm25" />
            <el-option label="PM10" value="pm10" />
          </el-select>
          <el-select v-model="filters.severity" placeholder="全部等级" clearable style="width: 130px" @change="loadList">
            <el-option label="轻度" value="mild" />
            <el-option label="中度" value="moderate" />
            <el-option label="重度" value="severe" />
          </el-select>
        </div>
      </el-card>
    </section>

    <section class="page-section anomaly-body">
      <div class="section-heading compact-heading">
        <span class="section-kicker">RECORDS</span>
        <h2 class="section-title">异常事件列表</h2>
      </div>

      <el-card class="table-card">
        <template #header>
          <div class="table-head">
            <div>
              <span>异常事件记录</span>
              <p>包含异常方向、严重度、状态与处理操作。</p>
            </div>
          </div>
        </template>
        <el-table :data="aqStore.anomalyList" stripe border v-loading="loading">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column label="城市" width="90">
            <template #default="{ row }">{{ getCityName(row.cityId) }}</template>
          </el-table-column>
          <el-table-column prop="metricName" label="指标" width="90">
            <template #default="{ row }">{{ row.metricName.toUpperCase() }}</template>
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
          <el-table-column prop="recordTime" label="时间" width="120">
            <template #default="{ row }">{{ row.recordTime.slice(0, 10) }}</template>
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
              <div class="action-row" v-if="row.status === 'pending'">
                <el-button type="success" size="small" @click="updateStatus(row.id, 'confirmed')">确认</el-button>
                <el-button type="info" size="small" @click="updateStatus(row.id, 'dismissed')">忽略</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useCityStore } from '@/stores/city'
import { useAirQualityStore } from '@/stores/airQuality'
import { anomalyApi } from '@/api/modules'
import AppHeader from '@/components/layout/AppHeader.vue'

const cityStore = useCityStore()
const aqStore = useAirQualityStore()
const loading = ref(false)

const filters = reactive({ city_id: null, metric: null, severity: null })

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
  padding-bottom: 28px;
}

.filter-card,
.table-card {
  background: rgba(255, 252, 247, 0.78) !important;
}

.filter-topbar,
.table-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}

.filter-kicker {
  font-family: var(--aq-mono);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--aq-accent);
}

.filter-title {
  margin-top: 10px;
  font-family: var(--aq-display);
  font-size: 30px;
  line-height: 1.15;
  color: var(--aq-ink);
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-top: 18px;
  align-items: center;
  flex-wrap: wrap;
}

.table-head p {
  margin-top: 4px;
  color: var(--aq-ink-soft);
}

.action-row {
  display: flex;
  gap: 8px;
}

@media (max-width: 1100px) {
  .filter-topbar {
    flex-direction: column;
  }
}
</style>
