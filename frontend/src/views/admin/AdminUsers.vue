<template>
  <div class="admin-users">
    <div class="toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索用户名/昵称"
        clearable
        style="width: 240px"
        @keyup.enter="load"
        @clear="load"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>新增用户
      </el-button>
    </div>

    <div class="panel">
      <el-table
        :data="list"
        v-loading="loading"
        empty-text="暂无数据"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="140" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.role === 'admin' ? 'success' : 'info'">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column prop="lastLoginAt" label="最后登录" min-width="160" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button size="small" type="warning" @click="openReset(row)">
              <el-icon><Key /></el-icon>重置密码
            </el-button>
            <el-button
              size="small"
              type="danger"
              :disabled="row.id === userStore.userInfo?.id"
              @click="handleDelete(row)"
            >
              <el-icon><Delete /></el-icon>删除
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
          :page-sizes="[10, 20, 50]"
          @current-change="onPageChange"
          @size-change="onSizeChange"
        />
      </div>
    </div>

    <!-- 新增/编辑 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增用户' : '编辑用户'"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        label-position="left"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item v-if="dialogMode === 'create'" label="密码" prop="password">
          <el-input v-model="formData.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="formData.nickname" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role">
            <el-option label="admin（管理员）" value="admin" />
            <el-option label="user（普通用户）" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="formData.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码 -->
    <el-dialog v-model="resetVisible" title="重置密码" width="380px">
      <el-form label-width="80px">
        <el-form-item label="账号">
          <span class="reset-username">{{ resetTarget?.username }}</span>
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="resetPassword" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitReset">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Edit, Delete, Key } from '@element-plus/icons-vue'
import { adminUserApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const loading = ref(false)
const list = ref([])
const total = ref(0)
const filters = reactive({ keyword: '', page: 1, size: 10 })

const dialogVisible = ref(false)
const dialogMode = ref('create')
const formRef = ref()
const formData = reactive({
  id: null,
  username: '',
  password: '',
  nickname: '',
  role: 'user',
  phone: '',
})
const submitting = ref(false)

const resetVisible = ref(false)
const resetTarget = ref(null)
const resetPassword = ref('')

const formRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  role: [{ required: true, trigger: 'change' }],
}

async function load() {
  loading.value = true
  try {
    const data = await adminUserApi.list({
      keyword: filters.keyword,
      page: filters.page,
      size: filters.size,
    })
    list.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(page) { filters.page = page; load() }
function onSizeChange(size) { filters.size = size; filters.page = 1; load() }

function resetForm() {
  Object.assign(formData, {
    id: null,
    username: '',
    password: '',
    nickname: '',
    role: 'user',
    phone: '',
  })
}

function openCreate() {
  resetForm()
  dialogMode.value = 'create'
  dialogVisible.value = true
}

function openEdit(row) {
  resetForm()
  Object.assign(formData, {
    id: row.id,
    username: row.username,
    nickname: row.nickname || '',
    role: row.role,
    phone: row.phone || '',
  })
  dialogMode.value = 'edit'
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await adminUserApi.create({
        username: formData.username,
        password: formData.password,
        nickname: formData.nickname,
        role: formData.role,
        phone: formData.phone,
      })
      ElMessage.success('创建成功')
    } else {
      await adminUserApi.update(formData.id, {
        nickname: formData.nickname,
        role: formData.role,
        phone: formData.phone,
      })
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    load()
  } finally {
    submitting.value = false
  }
}

function openReset(row) {
  resetTarget.value = row
  resetPassword.value = ''
  resetVisible.value = true
}

async function submitReset() {
  if (resetPassword.value.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  submitting.value = true
  try {
    await adminUserApi.resetPassword(resetTarget.value.id, resetPassword.value)
    ElMessage.success('密码已重置')
    resetVisible.value = false
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '确认', {
      type: 'warning',
    })
    await adminUserApi.remove(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    // 取消或失败
  }
}

load()
</script>

<style scoped>
.admin-users {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.reset-username {
  font-family: var(--font-mono);
  color: var(--primary);
}
</style>
