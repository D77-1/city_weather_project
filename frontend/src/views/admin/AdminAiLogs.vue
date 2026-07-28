<template>
  <div class="admin-ai-logs">
    <div class="toolbar">
      <el-input
        v-model="filters.sessionId"
        placeholder="会话 ID"
        clearable
        style="width: 220px"
        @keyup.enter="load"
        @clear="load"
      />
      <el-select v-model="filters.source" placeholder="来源" clearable style="width: 140px" @change="load">
        <el-option label="Web 前端" value="web" />
        <el-option label="微信小程序" value="miniapp" />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="datetimerange"
        range-separator="~"
        start-placeholder="起始时间"
        end-placeholder="截止时间"
        value-format="YYYY-MM-DD HH:mm:ss"
        style="width: 360px"
        @change="load"
      />
      <el-button @click="load">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <div class="panel">
      <el-table :data="list" v-loading="loading" empty-text="暂无 AI 对话日志">
        <el-table-column prop="createdAt" label="时间" width="150" />
        <el-table-column label="来源" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.source === 'miniapp' ? 'success' : ''">
              {{ row.source === 'miniapp' ? '小程序' : 'Web' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="modelName" label="模型" width="110" />
        <el-table-column label="城市" width="100">
          <template #default="{ row }">{{ row.cityName || '—' }}</template>
        </el-table-column>
        <el-table-column label="Tokens" width="90">
          <template #default="{ row }">
            <span class="num">{{ row.tokensUsed ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="90">
          <template #default="{ row }">
            <span class="num">{{ row.responseTimeMs ? `${row.responseTimeMs} ms` : '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="userMessagePreview" label="用户提问" min-width="280" show-overflow-tooltip />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">
              <el-icon><View /></el-icon>详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          background
          layout="total, prev, pager, next, sizes"
          :total="total"
          :current-page="filters.page"
          :page-size="filters.size"
          :page-sizes="[20, 50, 100]"
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </div>

    <el-drawer v-model="detailVisible" title="对话详情" size="560px">
      <div v-if="detail" class="detail-body">
        <div class="detail-meta">
          <div><b>会话 ID：</b><code>{{ detail.sessionId }}</code></div>
          <div><b>模型：</b>{{ detail.modelName }}</div>
          <div><b>来源：</b>{{ detail.source }}</div>
          <div><b>时间：</b>{{ detail.createdAt }}</div>
          <div><b>Tokens：</b>{{ detail.tokensUsed ?? '—' }} / <b>耗时：</b>{{ detail.responseTimeMs ?? '—' }} ms</div>
        </div>
        <el-divider />
        <div class="dialog-block">
          <div class="block-title">用户提问</div>
          <div class="block-content user-msg">{{ detail.userMessage }}</div>
        </div>
        <div class="dialog-block">
          <div class="block-title">AI 回答</div>
          <div class="block-content ai-msg">{{ detail.aiResponse }}</div>
        </div>
        <div v-if="detail.contextData" class="dialog-block">
          <div class="block-title">上下文数据</div>
          <pre class="block-content ctx-data">{{ JSON.stringify(detail.contextData, null, 2) }}</pre>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { Refresh, View } from '@element-plus/icons-vue'
import { adminAiLogApi } from '@/api/modules'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const filters = reactive({
  page: 1,
  size: 20,
  sessionId: '',
  source: null,
  startTime: '',
  endTime: '',
})
const dateRange = ref([])

const detailVisible = ref(false)
const detail = ref(null)

async function load() {
  loading.value = true
  try {
    if (Array.isArray(dateRange.value) && dateRange.value.length === 2) {
      filters.startTime = dateRange.value[0]
      filters.endTime = dateRange.value[1]
    } else {
      filters.startTime = ''
      filters.endTime = ''
    }
    const params = {}
    Object.entries(filters).forEach(([k, v]) => { if (v) params[k] = v })
    const data = await adminAiLogApi.list(params)
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(page) { filters.page = page; load() }
function onSizeChange(size) { filters.size = size; filters.page = 1; load() }

async function openDetail(row) {
  detail.value = null
  detailVisible.value = true
  detail.value = await adminAiLogApi.detail(row.id)
}

load()
</script>

<style scoped>
.admin-ai-logs {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.panel {
  padding: 16px 18px;
  border-radius: 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 14px;
}

.num {
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.detail-body { padding: 0 4px; }

.detail-meta {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 2;
}

.detail-meta code {
  font-family: var(--font-mono);
  font-size: 12px;
  background: rgba(39, 211, 195, 0.12);
  color: var(--primary);
  padding: 2px 6px;
  border-radius: 4px;
}

.dialog-block {
  margin-bottom: 16px;
}

.block-title {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
  letter-spacing: 0.5px;
}

.block-content {
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(10, 21, 37, 0.6);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.user-msg { border-left: 2px solid rgba(110, 168, 255, 0.45); }
.ai-msg { border-left: 2px solid rgba(39, 211, 195, 0.5); }

.ctx-data {
  font-family: var(--font-mono);
  font-size: 12px;
  max-height: 300px;
  overflow: auto;
}
</style>
