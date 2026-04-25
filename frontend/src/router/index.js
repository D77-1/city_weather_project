import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '数据看板' },
  },
  {
    path: '/analysis',
    name: 'Analysis',
    component: () => import('@/views/Analysis.vue'),
    meta: { title: '数据分析' },
  },
  {
    path: '/city/:id',
    name: 'CityDetail',
    component: () => import('@/views/CityDetail.vue'),
    meta: { title: '城市详情' },
  },
  {
    path: '/compare',
    name: 'Compare',
    component: () => import('@/views/Compare.vue'),
    meta: { title: '城市对比' },
  },
  {
    path: '/report',
    name: 'Report',
    component: () => import('@/views/Report.vue'),
    meta: { title: '数据报告' },
  },
  {
    path: '/anomaly',
    name: 'AnomalyList',
    component: () => import('@/views/AnomalyList.vue'),
    meta: { title: '异常管理' },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/admin/Login.vue'),
    meta: { title: '管理员登录', hideNav: true },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAdmin: true, hideNav: true },
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/AdminDashboard.vue'),
        meta: { title: '管理仪表盘', requiresAdmin: true, hideNav: true },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsers.vue'),
        meta: { title: '用户管理', requiresAdmin: true, hideNav: true },
      },
      {
        path: 'anomaly-review',
        name: 'AdminAnomalyReview',
        component: () => import('@/views/admin/AdminAnomalyReview.vue'),
        meta: { title: '异常审核', requiresAdmin: true, hideNav: true },
      },
      {
        path: 'ai-logs',
        name: 'AdminAiLogs',
        component: () => import('@/views/admin/AdminAiLogs.vue'),
        meta: { title: 'AI日志审计', requiresAdmin: true, hideNav: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  document.title = `${to.meta.title || ''} - 空气质量可视化系统`

  if (!to.meta.requiresAdmin) return true

  const userStore = useUserStore()
  if (!userStore.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  // 有 token 但无 user 信息，拉一次
  if (!userStore.userInfo) {
    await userStore.fetchMe()
  }
  if (!userStore.isAdmin) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
