import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: '数据看板' },
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
    meta: { title: '异常事件' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  document.title = `${to.meta.title || ''} - 空气质量可视化系统`
})

export default router
