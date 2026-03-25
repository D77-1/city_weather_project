<template>
  <div class="anomaly-page">
    <AppHeader />

    <div style="padding: 16px 24px">
      <el-page-header @back="$router.push('/')" content="异常数据检测" />

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select v-model="filters.city_id" placeholder="全部城市" clearable style="width: 150px" @change="loadList">
          <el-option v-for="c in cityStore.cities" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-select v-model="filters.metric" placeholder="全部指标" clearable style="width: 120px" @change="loadList">
          <el-option label="AQI" value="aqi" />
          <el-option label="PM2.5" value="pm25" />
          <el-option label="PM10" value="pm10" />
        </el-select>
        <el-select v-model="filters.severity" placeholder="全部等级" clearable style="width: 120px" @change="loadList">
          <el-option label="轻度" value="mild" />
          <el-option label="中度" value="moderate" />
          <el-option label="重度" value="severe" />
        </el-select>
        <el-button type="primary" @click="runDetectAll">执行异常检测</el-button>
      </div>

      <!-- 数据表格 -->
      <el-table :data="aqStore.anomalyList" stripe border style="margin-top: 12px" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="城市" width="80">
          <template #default="{ row }">{{ getCityName(row.cityId) }}</template>
        </el-table-column>
        <el-table-column prop="metricName" label="指标" width="80">
          <template #default="{ row }">{{ row.metricName.toUpperCase() }}</template>
        </el-table-column>
        <el-table-column prop="actualValue" label="实际值" width="80" />
        <el-table-column label="正常范围" width="140">
          <template #default="{ row }">{{ row.lowerBound }} ~ {{ row.upperBound }}</template>
        </el-table-column>
        <el-table-column prop="anomalyType" label="方向" width="70">
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
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" type="success" size="small" @click="updateStatus(row.id, 'confirmed')">确认</el-button>
            <el-button v-if="row.status === 'pending'" type="info" size="small" @click="updateStatus(row.id, 'dismissed')">忽略</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
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
  min-height: 100vh;
  background: var(--bg-page, #eae6e1);
  color: var(--text-primary, #2c2c2c);
  transition: background-color 0.4s var(--bounce), color 0.4s var(--bounce);
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  align-items: center;
}
</style>
