<template>
  <div class="anomaly-page page-shell">
    <AppHeader />

    <div class="page-content">
      <section class="page-hero panel-surface">
        <el-page-header @back="goHome" content="异常归因分析" class="hero-header" />
        <div class="hero-grid">
          <div>
            <span class="panel-kicker">Attribution Center</span>
            <h2 class="hero-title">异常事件归因分析中心</h2>
            <p class="hero-desc">基于 IQR / Z-score / MAD 多方法检测的异常事件，结合大模型做成因、健康影响与处置建议的自动归因。标记为误报的记录将在下一次检测时从分位数估计中剔除，形成人机协同的反馈闭环。</p>
          </div>
          <div class="hero-side-note">
            <span class="side-label">当前记录数</span>
            <strong>{{ aqStore.anomalyList.length }}</strong>
            <span class="side-caption">基于当前筛选条件</span>
          </div>
        </div>
      </section>

      <div class="summary-grid">
        <div class="summary-card panel-surface">
          <span class="summary-label">待归因</span>
          <strong class="summary-value">{{ anomalySummary.pending }}</strong>
          <span class="summary-foot">未生成 AI 分析</span>
        </div>
        <div class="summary-card panel-surface">
          <span class="summary-label">严重事件</span>
          <strong class="summary-value danger">{{ anomalySummary.severe }}</strong>
          <span class="summary-foot">偏离幅度 ≥ 3×IQR</span>
        </div>
        <div class="summary-card panel-surface">
          <span class="summary-label">已归因</span>
          <strong class="summary-value success">{{ anomalySummary.confirmed }}</strong>
          <span class="summary-foot">已生成成因与建议</span>
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
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 140px" @change="loadList">
            <el-option label="待归因" value="pending" />
            <el-option label="已归因" value="confirmed" />
            <el-option label="误报" value="dismissed" />
          </el-select>
          <el-button v-if="canEdit" type="primary" class="detect-btn" @click="runDetectAll">执行异常检测</el-button>
          <router-link v-else to="/login" class="login-cta">
            登录管理员后可执行检测 / 审核 →
          </router-link>
        </div>
      </section>

      <section class="table-panel panel-surface">
        <div class="table-head">
          <div>
            <span class="panel-kicker">Anomaly Ledger</span>
            <h3>异常事件列表</h3>
          </div>
          <span class="table-tip">点击任意一行展开 AI 归因分析详情</span>
        </div>
        <el-table
          :data="aqStore.anomalyList"
          stripe
          border
          style="margin-top: 12px"
          v-loading="loading"
          @row-click="openDetail"
          row-class-name="clickable-row"
        >
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
          <el-table-column label="偏离" width="90">
            <template #default="{ row }">
              <span :class="deviationClass(row)">{{ formatDeviation(row) }}</span>
            </template>
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
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <template v-if="canEdit">
                <el-button
                  v-if="row.status !== 'dismissed'"
                  type="primary"
                  size="small"
                  :loading="analyzingId === row.id"
                  @click.stop="runAnalyze(row)"
                >{{ row.aiAnalysis ? '查看归因' : 'AI 归因' }}</el-button>
                <el-button
                  v-if="row.status !== 'dismissed'"
                  size="small"
                  @click.stop="markDismissed(row)"
                >标为误报</el-button>
                <el-button
                  v-else
                  size="small"
                  @click.stop="restoreDismissed(row)"
                >撤销误报</el-button>
              </template>
              <span v-else class="guest-hint">仅管理员可操作</span>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>

    <el-drawer v-model="drawerVisible" :size="520" title="异常归因详情" direction="rtl">
      <div v-if="detail" class="detail-pane">
        <div class="detail-meta">
          <div class="meta-row"><span>城市</span><strong>{{ getCityName(detail.cityId) }}</strong></div>
          <div class="meta-row"><span>指标 / 时间</span><strong>{{ formatMetricName(detail.metricName) }} · {{ formatRecordDate(detail.recordTime) }}</strong></div>
          <div class="meta-row"><span>实际值</span><strong>{{ detail.actualValue }}</strong></div>
          <div class="meta-row"><span>IQR 正常范围</span><strong>{{ detail.lowerBound }} ~ {{ detail.upperBound }}</strong></div>
          <div class="meta-row"><span>偏离幅度</span><strong :class="deviationClass(detail)">{{ formatDeviation(detail) }}</strong></div>
          <div class="meta-row"><span>严重度 / 方向</span>
            <strong>
              <el-tag :type="severityType(detail.severity)" size="small" style="margin-right:6px">{{ { severe: '严重', moderate: '中度', mild: '轻度' }[detail.severity] }}</el-tag>
              <el-tag :type="detail.anomalyType === 'high' ? 'danger' : 'primary'" size="small">{{ detail.anomalyType === 'high' ? '偏高' : '偏低' }}</el-tag>
            </strong>
          </div>
        </div>

        <div class="detail-block">
          <div class="block-head">
            <h4>AI 归因分析</h4>
            <el-button
              v-if="canEdit"
              size="small"
              :loading="analyzingId === detail.id"
              @click="runAnalyze(detail, true)"
            >{{ detail.aiAnalysis ? '重新生成' : '生成分析' }}</el-button>
          </div>
          <div v-if="detail.aiAnalysis" class="ai-content">{{ detail.aiAnalysis }}</div>
          <el-empty v-else :description="canEdit ? '尚未生成归因分析，点击右上按钮生成' : '尚未生成归因分析（仅管理员可生成）'" :image-size="80" />
        </div>

        <div v-if="canEdit" class="detail-actions">
          <el-button
            v-if="detail.status !== 'dismissed'"
            type="warning"
            plain
            @click="markDismissed(detail)"
          >标为误报（下次检测将剔除该点）</el-button>
          <el-button
            v-else
            plain
            @click="restoreDismissed(detail)"
          >撤销误报</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useCityStore } from '@/stores/city'
import { useAirQualityStore } from '@/stores/airQuality'
import { useUserStore } from '@/stores/user'
import { anomalyApi } from '@/api/modules'
import AppHeader from '@/components/layout/AppHeader.vue'

const router = useRouter()
const cityStore = useCityStore()
const aqStore = useAirQualityStore()
const userStore = useUserStore()
const loading = ref(false)
const analyzingId = ref(null)
const drawerVisible = ref(false)
const detail = ref(null)

const canEdit = computed(() => userStore.isAdmin)

function goHome() {
  router.push('/')
}

const filters = reactive({ city_id: null, metric: null, severity: null, status: null })

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
    if (filters.status) params.status = filters.status
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
    ElMessage.success('检测完成，误报点已从分位数估计中剔除')
  } finally {
    loading.value = false
  }
}

async function runAnalyze(row, force = false) {
  analyzingId.value = row.id
  try {
    const updated = await anomalyApi.analyze(row.id, { force })
    Object.assign(row, updated)
    if (detail.value && detail.value.id === row.id) detail.value = { ...updated }
    if (!drawerVisible.value) openDetail(updated)
    ElMessage.success('归因分析已生成')
  } catch (e) {
    ElMessage.error('归因分析失败，请检查 AI 服务配置')
  } finally {
    analyzingId.value = null
  }
}

async function markDismissed(row) {
  const updated = await anomalyApi.updateStatus(row.id, { status: 'dismissed' })
  Object.assign(row, updated)
  if (detail.value && detail.value.id === row.id) detail.value = { ...updated }
  ElMessage.success('已标记为误报，下次检测会自动剔除该点')
}

async function restoreDismissed(row) {
  const updated = await anomalyApi.updateStatus(row.id, { status: 'pending' })
  Object.assign(row, updated)
  if (detail.value && detail.value.id === row.id) detail.value = { ...updated }
  ElMessage.success('已撤销误报标记')
}

function openDetail(row) {
  detail.value = { ...row }
  drawerVisible.value = true
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

function formatDeviation(row) {
  if (!row) return '--'
  const bound = row.anomalyType === 'high' ? row.upperBound : row.lowerBound
  const diff = Number(row.actualValue) - Number(bound)
  const sign = diff >= 0 ? '+' : ''
  return `${sign}${diff.toFixed(1)}`
}

function deviationClass(row) {
  if (!row) return ''
  return row.anomalyType === 'high' ? 'deviation-high' : 'deviation-low'
}

function severityType(s) {
  if (s === 'severe') return 'danger'
  if (s === 'moderate') return 'warning'
  return 'info'
}

function statusLabel(s) {
  return { pending: '待归因', confirmed: '已归因', dismissed: '误报' }[s] || s
}

function statusTagType(s) {
  if (s === 'confirmed') return 'success'
  if (s === 'dismissed') return 'info'
  return 'warning'
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

.login-cta {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(39, 211, 195, 0.08);
  border: 1px solid rgba(39, 211, 195, 0.25);
  color: var(--primary);
  font-size: 13px;
  text-decoration: none;
  transition: background 0.2s ease;
}

.login-cta:hover {
  background: rgba(39, 211, 195, 0.14);
}

.guest-hint {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.table-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
}

.table-tip {
  font-size: 12px;
  color: var(--text-muted);
}

:deep(.clickable-row) {
  cursor: pointer;
}

.deviation-high {
  color: var(--danger);
  font-weight: 600;
}

.deviation-low {
  color: var(--primary-light);
  font-weight: 600;
}

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
}

.ai-content {
  white-space: pre-wrap;
  line-height: 1.85;
  font-size: 13.5px;
  color: var(--text-secondary);
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
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
