<template>
  <div class="admin-anomaly-review">
    <div class="toolbar panel-surface">
      <el-select v-model="filters.city_id" placeholder="城市" clearable style="width: 160px" @change="load">
        <el-option
          v-for="c in cities"
          :key="c.id"
          :label="c.name"
          :value="c.id"
        />
      </el-select>
      <el-select v-model="filters.metric" placeholder="指标" clearable style="width: 120px" @change="load">
        <el-option label="AQI" value="aqi" />
        <el-option label="PM2.5" value="pm25" />
        <el-option label="PM10" value="pm10" />
        <el-option label="O3" value="o3" />
        <el-option label="NO2" value="no2" />
        <el-option label="SO2" value="so2" />
        <el-option label="CO" value="co" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px" @change="load">
        <el-option label="待处理" value="pending" />
        <el-option label="已确认" value="confirmed" />
        <el-option label="已忽略" value="dismissed" />
      </el-select>
      <el-select v-model="filters.severity" placeholder="严重程度" clearable style="width: 130px" @change="load">
        <el-option label="轻度" value="mild" />
        <el-option label="中度" value="moderate" />
        <el-option label="重度" value="severe" />
      </el-select>
      <el-button @click="load">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>

      <div class="batch-bar">
        <el-tag v-if="selected.length" type="info">已选 {{ selected.length }} 条</el-tag>
        <el-button
          size="default"
          type="danger"
          :disabled="!selected.length"
          @click="batchReview('confirmed')"
        >批量确认异常</el-button>
        <el-button
          size="default"
          type="warning"
          :disabled="!selected.length"
          @click="batchReview('dismissed')"
        >批量标记误报</el-button>
      </div>
    </div>

    <div class="panel">
      <el-table
        :data="list"
        v-loading="loading"
        empty-text="暂无异常事件"
        @selection-change="onSelectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="recordTime" label="时间" width="150" />
        <el-table-column label="城市" width="100">
          <template #default="{ row }">{{ cityMap[row.cityId] || row.cityId }}</template>
        </el-table-column>
        <el-table-column prop="metricName" label="指标" width="80" />
        <el-table-column label="实际值" width="100">
          <template #default="{ row }">
            <span class="num">{{ row.actualValue }}</span>
          </template>
        </el-table-column>
        <el-table-column label="阈值范围" min-width="150">
          <template #default="{ row }">
            <span class="range">[{{ row.lowerBound }}, {{ row.upperBound }}]</span>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.anomalyType === 'high' ? 'danger' : 'warning'">
              {{ row.anomalyType === 'high' ? '偏高' : '偏低' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="严重程度" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="severityType(row.severity)">
              {{ severityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核人" width="100">
          <template #default="{ row }">
            {{ row.reviewerName || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="审核时间" width="150">
          <template #default="{ row }">
            {{ row.reviewedAt || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="AI 归因" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.aiAnalysis"
              size="small"
              @click="openAnalysis(row)"
            >
              <el-icon><View /></el-icon>查看
            </el-button>
            <el-button
              v-else
              size="small"
              type="primary"
              :loading="analyzingId === row.id"
              @click="generateAnalysis(row)"
            >
              <el-icon v-if="analyzingId !== row.id"><MagicStick /></el-icon>生成
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- AI 归因详情 -->
    <el-drawer v-model="analysisVisible" :size="520" title="AI 异常归因" direction="rtl">
      <div v-if="currentAnalysis" class="detail-pane">
        <div class="detail-meta">
          <div class="meta-row"><span>城市</span><strong>{{ cityMap[currentAnalysis.cityId] || '—' }}</strong></div>
          <div class="meta-row"><span>指标 / 时间</span><strong>{{ metricLabel(currentAnalysis.metricName) }} · {{ currentAnalysis.recordTime }}</strong></div>
          <div class="meta-row"><span>实际值</span><strong class="num">{{ currentAnalysis.actualValue }}</strong></div>
          <div class="meta-row"><span>IQR 正常范围</span><strong class="num">{{ currentAnalysis.lowerBound }} ~ {{ currentAnalysis.upperBound }}</strong></div>
          <div class="meta-row">
            <span>严重度 / 方向</span>
            <strong>
              <el-tag :type="severityType(currentAnalysis.severity)" size="small" style="margin-right:6px">{{ severityLabel(currentAnalysis.severity) }}</el-tag>
              <el-tag :type="currentAnalysis.anomalyType === 'high' ? 'danger' : 'primary'" size="small">{{ currentAnalysis.anomalyType === 'high' ? '偏高' : '偏低' }}</el-tag>
            </strong>
          </div>
        </div>

        <div class="detail-block">
          <div class="block-head">
            <h4>AI 归因分析</h4>
          </div>
          <div v-if="currentAnalysis.aiAnalysis" class="ai-content">{{ currentAnalysis.aiAnalysis }}</div>
          <el-empty v-else description="尚未生成归因分析" :image-size="80" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, View, MagicStick } from '@element-plus/icons-vue'
import { anomalyApi, cityApi, adminAnomalyApi } from '@/api/modules'

const loading = ref(false)
const list = ref([])
const selected = ref([])
const cities = ref([])
const cityMap = ref({})

const filters = reactive({
  city_id: null,
  metric: null,
  status: 'pending',
  severity: null,
})

const analysisVisible = ref(false)
const currentAnalysis = ref(null)
const analyzingId = ref(null)

async function loadCities() {
  cities.value = await cityApi.getList()
  cityMap.value = Object.fromEntries(cities.value.map(c => [c.id, c.name]))
}

async function load() {
  loading.value = true
  try {
    const params = { limit: 200 }
    Object.keys(filters).forEach(k => {
      if (filters[k]) params[k] = filters[k]
    })
    list.value = await anomalyApi.getList(params)
  } finally {
    loading.value = false
  }
}

function onSelectionChange(rows) {
  selected.value = rows
}

async function batchReview(action) {
  if (!selected.value.length) return
  const actionLabel = action === 'confirmed' ? '确认为异常' : '标记为误报'
  try {
    await ElMessageBox.confirm(
      `将 ${selected.value.length} 条异常事件${actionLabel}？${action === 'dismissed' ? '（误报的点将在下一轮 IQR 检测时被剔除）' : ''}`,
      '确认批量操作',
      { type: 'warning' }
    )
  } catch {
    return
  }

  const ids = selected.value.map(r => r.id)
  const data = await adminAnomalyApi.batchReview(ids, action)
  ElMessage.success(`已${actionLabel} ${data.updated} 条`)
  selected.value = []
  load()
}

function openAnalysis(row) {
  currentAnalysis.value = row
  analysisVisible.value = true
}

async function generateAnalysis(row) {
  analyzingId.value = row.id
  try {
    const updated = await anomalyApi.analyze(row.id)
    Object.assign(row, updated)
    currentAnalysis.value = row
    analysisVisible.value = true
    ElMessage.success('AI 归因已生成')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '归因生成失败')
  } finally {
    analyzingId.value = null
  }
}

function severityLabel(s) { return { mild: '轻度', moderate: '中度', severe: '重度' }[s] || s }
function severityType(s) { return { mild: '', moderate: 'warning', severe: 'danger' }[s] || '' }
function statusLabel(s) { return { pending: '待处理', confirmed: '已确认', dismissed: '已忽略' }[s] || s }
function statusType(s) { return { pending: 'warning', confirmed: 'danger', dismissed: 'info' }[s] || '' }
function metricLabel(m) {
  return ({ aqi: 'AQI', pm25: 'PM2.5', pm10: 'PM10', so2: 'SO₂', no2: 'NO₂', co: 'CO', o3: 'O₃' })[m] || (m ? m.toUpperCase() : '—')
}

onMounted(async () => {
  await loadCities()
  load()
})
</script>

<style scoped>
.admin-anomaly-review {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.panel {
  padding: 16px 18px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

.num, .range {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.range { color: var(--text-muted); font-size: 12px; }

.detail-pane {
  padding: 0 20px 20px;
  display: grid;
  gap: 18px;
}

.detail-meta {
  display: grid;
  gap: 10px;
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  background: rgba(7, 18, 31, 0.55);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.meta-row span {
  color: var(--text-muted);
}

.meta-row strong {
  color: var(--text-primary);
  font-weight: 600;
}

.detail-block {
  display: grid;
  gap: 10px;
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  background: rgba(7, 18, 31, 0.55);
}

.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.block-head h4 {
  margin: 0;
  font-size: 15px;
  color: var(--text-primary);
}

.ai-content {
  white-space: pre-wrap;
  line-height: 1.85;
  font-size: 13.5px;
  color: var(--text-secondary);
}

:deep(.el-drawer) {
  background: linear-gradient(180deg, rgba(10, 22, 37, 0.96), rgba(6, 14, 24, 0.96));
  color: var(--text-primary);
  backdrop-filter: blur(18px);
  border-left: 1px solid var(--border-color);
}

:deep(.el-drawer__header) {
  margin-bottom: 0;
  padding: 20px 22px;
  color: var(--text-primary);
  font-weight: 600;
  letter-spacing: 0.04em;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(135deg, rgba(127, 246, 234, 0.08), transparent 60%);
}

:deep(.el-drawer__title) {
  color: var(--text-primary);
  font-size: 16px;
}

:deep(.el-drawer__close-btn) {
  color: var(--text-secondary);
}

:deep(.el-drawer__close-btn:hover) {
  color: var(--primary-light);
}

:deep(.el-drawer__body) {
  padding: 0;
  background: transparent;
  color: var(--text-primary);
}
</style>
