<template>
  <div class="login-page">
    <div class="login-card panel-surface">
      <div class="login-brand">
        <div class="brand-mark">AQ</div>
        <div class="brand-title">
          <h1>管理员后台</h1>
          <p>城市空气质量可视化与趋势预测系统</p>
        </div>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="form.username"
            size="large"
            placeholder="请输入用户名"
            autocomplete="username"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            size="large"
            placeholder="请输入密码"
            show-password
            autocomplete="current-password"
            :prefix-icon="Lock"
            @keyup.enter="handleSubmit"
          />
        </el-form-item>

        <el-button
          type="primary"
          size="large"
          class="login-btn"
          :loading="loading"
          native-type="submit"
          @click="handleSubmit"
        >登 录</el-button>
      </el-form>

      <div class="login-hint">
        首次部署默认账号 <code>admin</code> / <code>admin123</code>，登录后请在「用户管理」修改密码
      </div>

      <router-link class="login-back" to="/">返回门户首页 →</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
}

async function handleSubmit() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const user = await userStore.login(form.username, form.password)
    ElMessage.success(`欢迎，${user.nickname || user.username}`)
    const redirect = route.query.redirect || '/admin/dashboard'
    router.replace(redirect)
  } catch (e) {
    // 错误消息由 axios 拦截器统一提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 440px;
  padding: 40px 36px 32px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: var(--bg-card-strong);
  box-shadow: var(--shadow);
  backdrop-filter: blur(16px);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}

.brand-mark {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: rgba(39, 211, 195, 0.12);
  border: 1px solid rgba(39, 211, 195, 0.32);
  color: var(--primary);
  font-weight: 700;
  font-size: 18px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-title h1 {
  font-size: 20px;
  color: var(--text-primary);
  margin-bottom: 4px;
  font-weight: 600;
}

.brand-title p {
  font-size: 12px;
  color: var(--text-muted);
}

.login-btn {
  width: 100%;
  margin-top: 6px;
  height: 44px;
  font-size: 15px;
  letter-spacing: 4px;
}

.login-hint {
  margin-top: 20px;
  font-size: 12px;
  color: var(--text-muted);
  text-align: center;
  line-height: 1.7;
}

.login-hint code {
  padding: 1px 6px;
  background: rgba(39, 211, 195, 0.1);
  border-radius: 4px;
  color: var(--primary);
  font-family: var(--font-mono);
  font-size: 12px;
}

.login-back {
  display: block;
  margin-top: 18px;
  text-align: center;
  font-size: 12px;
  color: var(--text-secondary);
  text-decoration: none;
  transition: color 0.2s ease;
}

.login-back:hover {
  color: var(--primary);
}
</style>
