<template>
  <div class="admin-dashboard">
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="8" :md="6" v-for="kpi in kpis" :key="kpi.label">
        <div class="kpi-card">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value" :style="kpi.valueStyle">{{ kpi.value }}</div>
          <div class="kpi-sub">{{ kpi.sub }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="panel-row">
      <el-col :xs="24" :md="14">
        <div class="panel">
          <div class="panel-head">
            <h3>近 7 天异常事件趋势</h3>
          </div>
          <div ref="trendRef" class="trend-chart"></div>
        </div>
      </el-col>

      <el-col :xs="24" :md="10">
        <div class="panel">
          <div class="panel-head">
            <h3>近期登录</h3>
            <span class="panel-hint">最近 5 位用户</span>
          </div>
          <el-table
            :data="stats?.recentLogins || []"
            size="small"
            empty-text="暂无登录记录"
          >
            <el-table-column prop="username" label="账号" width="100" />
            <el-table-column prop="nickname" label="昵称" />
            <el-table-column prop="role" label="角色" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="row.role === 'admin' ? 'success' : 'info'">
                  {{ row.role }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="lastLoginAt" label="最后登录" />
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="panel-row">
      <el-col :xs="24" :md="12">
        <div class="panel">
          <div class="panel-head">
            <h3>异常事件状态分布</h3>
          </div>
          <div class="status-grid">
            <div class="status-cell status-pending">
              <div class="status-count">{{ stats?.anomalies?.pending ?? 0 }}</div>
              <div class="status-label">待处理</div>
            </div>
            <div class="status-cell status-confirmed">
              <div class="status-count">{{ stats?.anomalies?.confirmed ?? 0 }}</div>
              <div class="status-label">已确认</div>
            </div>
            <div class="status-cell status-dismissed">
              <div class="status-count">{{ stats?.anomalies?.dismissed ?? 0 }}</div>
              <div class="status-label">已忽略</div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :md="12">
        <div class="panel">
          <div class="panel-head">
            <h3>AI 服务使用情况</h3>
          </div>
          <div class="ai-stats">
            <div class="ai-stat">
              <span class="ai-label">总调用次数</span>
              <span class="ai-val">{{ stats?.aiCalls?.total ?? 0 }}</span>
            </div>
            <div class="ai-stat">
              <span class="ai-label">今日调用</span>
              <span class="ai-val">{{ stats?.aiCalls?.today ?? 0 }}</span>
            </div>
            <div class="ai-stat">
              <span class="ai-label">累计消耗 Token</span>
              <span class="ai-val">{{ (stats?.aiCalls?.tokensTotal ?? 0).toLocaleString() }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { adminStatsApi } from '@/api/modules'

const stats = ref(null)
const trendRef = ref(null)
let trendChart = null

const kpis = computed(() => {
  if (!stats.value) {
    return [
      { label: '数据总记录', value: '--', sub: '加载中', valueStyle: {} },
      { label: '在监城市', value: '--', sub: '加载中', valueStyle: {} },
      { label: '活跃站点', value: '--', sub: '加载中', valueStyle: {} },
      { label: '待审核异常', value: '--', sub: '加载中', valueStyle: {} },
      { label: '注册用户', value: '--', sub: '加载中', valueStyle: {} },
      { label: '最新数据时间', value: '--', sub: '加载中', valueStyle: {} },
    ]
  }
  const s = stats.value
  return [
    {
      label: '数据总记录',
      value: (s.totalRecords ?? 0).toLocaleString(),
      sub: '空气质量表条数',
      valueStyle: { color: 'var(--text-primary)' },
    },
    {
      label: '在监城市',
      value: s.activeCities ?? 0,
      sub: `${s.activeStations ?? 0} 个活跃站点`,
      valueStyle: { color: 'var(--primary)' },
    },
    {
      label: '待审核异常',
      value: s.anomalies?.pending ?? 0,
      sub: `累计 ${s.anomalies?.total ?? 0} 条`,
      valueStyle: {
        color: (s.anomalies?.pending ?? 0) > 0 ? 'var(--warning)' : 'var(--success)',
      },
    },
    {
      label: '今日 AI 调用',
      value: s.aiCalls?.today ?? 0,
      sub: `累计 ${s.aiCalls?.total ?? 0} 次`,
      valueStyle: { color: 'var(--accent)' },
    },
    {
      label: '注册用户',
      value: s.users?.total ?? 0,
      sub: `${s.users?.admin ?? 0} 位管理员`,
      valueStyle: { color: 'var(--text-primary)' },
    },
    {
      label: '最新数据时间',
      value: s.latestRecordTime ? s.latestRecordTime.slice(5, 16) : '--',
      sub: s.latestRecordTime ? '来源 Open-Meteo' : '暂无数据',
      valueStyle: { color: 'var(--text-secondary)', fontSize: '20px' },
    },
  ]
})

async function load() {
  try {
    stats.value = await adminStatsApi.get()
    await nextTick()
    renderTrend()
  } catch (e) {
    ElMessage.error('仪表盘数据加载失败')
  }
}

function renderTrend() {
  if (!trendRef.value) return
  if (!trendChart) trendChart = echarts.init(trendRef.value)

  const data = stats.value?.anomalyTrend7d || []
  trendChart.setOption({
    grid: { top: 24, right: 16, bottom: 32, left: 40 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLine: { lineStyle: { color: 'var(--border-color)' } },
      axisLabel: { color: '#b7c8dc', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { lineStyle: { color: 'var(--border-color)' } },
      splitLine: { lineStyle: { color: 'rgba(124,154,188,0.12)' } },
      axisLabel: { color: '#b7c8dc', fontSize: 11 },
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.count),
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(39,211,195,0.85)' },
            { offset: 1, color: 'rgba(39,211,195,0.25)' },
          ],
        },
        borderRadius: [6, 6, 0, 0],
      },
      barMaxWidth: 28,
    }],
  })
}

function handleResize() { trendChart?.resize() }

onMounted(() => {
  load()
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
})
</script>

<style scoped>
.admin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kpi-row {
  margin-bottom: 4px;
}

.kpi-card {
  padding: 18px 20px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  margin-bottom: 12px;
  min-height: 110px;
}

.kpi-label {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.kpi-value {
  margin-top: 8px;
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 600;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}

.kpi-sub {
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-muted);
}

.panel-row {
  margin-bottom: 4px;
}

.panel {
  padding: 18px 20px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  margin-bottom: 12px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.panel-head h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.panel-hint {
  font-size: 11px;
  color: var(--text-muted);
}

.trend-chart {
  height: 240px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.status-cell {
  padding: 18px 14px;
  border-radius: 10px;
  text-align: center;
  border: 1px solid var(--border-color);
  background: rgba(10, 21, 37, 0.5);
}

.status-count {
  font-family: var(--font-mono);
  font-size: 26px;
  font-weight: 600;
}

.status-label {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
}

.status-pending .status-count { color: var(--warning); }
.status-confirmed .status-count { color: var(--danger); }
.status-dismissed .status-count { color: var(--text-secondary); }

.ai-stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(10, 21, 37, 0.5);
  border: 1px solid var(--border-color);
}

.ai-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.ai-val {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 600;
  color: var(--primary);
}
</style>
