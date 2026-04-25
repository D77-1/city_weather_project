<template>
  <div class="admin-layout">
    <aside class="admin-side">
      <div class="side-brand">
        <div class="brand-mark">AQ</div>
        <div class="brand-text">
          <div class="brand-name">管理员后台</div>
          <div class="brand-sub">Air Quality Admin</div>
        </div>
      </div>

      <el-menu
        class="side-menu"
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="#b7c8dc"
        active-text-color="#27d3c3"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/anomaly-review">
          <el-icon><Warning /></el-icon>
          <span>异常审核</span>
        </el-menu-item>
        <el-menu-item index="/admin/ai-logs">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 日志审计</span>
        </el-menu-item>
      </el-menu>

      <div class="side-foot">
        <router-link class="portal-link" to="/">← 返回门户</router-link>
      </div>
    </aside>

    <section class="admin-main">
      <header class="admin-topbar">
        <div class="topbar-left">
          <h2>{{ currentTitle }}</h2>
        </div>
        <div class="topbar-right">
          <span class="user-badge">
            <el-icon><User /></el-icon>
            {{ userStore.userInfo?.nickname || userStore.userInfo?.username || '管理员' }}
            <span class="role-tag">{{ userStore.userInfo?.role || 'admin' }}</span>
          </span>
          <el-button type="danger" plain size="small" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            <span>退出</span>
          </el-button>
        </div>
      </header>

      <main class="admin-content">
        <router-view />
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Odometer,
  User,
  Warning,
  ChatDotRound,
  SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta.title || '管理员后台')

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    userStore.logout()
    ElMessage.success('已退出登录')
    router.replace('/login')
  } catch (e) {
    // 用户取消
  }
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: flex;
}

.admin-side {
  width: 232px;
  flex-shrink: 0;
  background: var(--bg-card-strong);
  border-right: 1px solid var(--border-color);
  padding: 22px 0;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
  backdrop-filter: blur(14px);
}

.side-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 22px 22px;
  border-bottom: 1px solid var(--border-color);
}

.brand-mark {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(39, 211, 195, 0.12);
  border: 1px solid rgba(39, 211, 195, 0.3);
  color: var(--primary);
  font-weight: 700;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.brand-sub {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  margin-top: 2px;
}

.side-menu {
  flex: 1;
  padding-top: 14px;
  border-right: none !important;
}

.side-menu :deep(.el-menu-item) {
  margin: 4px 12px;
  border-radius: 10px;
  height: 44px;
  line-height: 44px;
}

.side-menu :deep(.el-menu-item:hover) {
  background: rgba(39, 211, 195, 0.08) !important;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: rgba(39, 211, 195, 0.14) !important;
}

.side-foot {
  padding: 14px 22px 4px;
  border-top: 1px solid var(--border-color);
}

.portal-link {
  font-size: 12px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color 0.2s ease;
}

.portal-link:hover {
  color: var(--primary);
}

.admin-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-topbar {
  height: 62px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-color);
  background: rgba(10, 21, 37, 0.55);
  backdrop-filter: blur(10px);
}

.topbar-left h2 {
  font-size: 17px;
  color: var(--text-primary);
  font-weight: 600;
  margin: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(10, 21, 37, 0.6);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 13px;
}

.role-tag {
  font-family: var(--font-mono);
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(39, 211, 195, 0.12);
  color: var(--primary);
  letter-spacing: 0.5px;
  margin-left: 4px;
}

.admin-content {
  flex: 1;
  padding: 24px 28px;
  overflow-y: auto;
}
</style>
