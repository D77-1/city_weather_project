import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 25000,
  headers: { 'Content-Type': 'application/json' },
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 处理 401（登录过期/未登录）—— 避免循环依赖，动态 import
function handleUnauthorized(msg) {
  ElMessage.error(msg || '登录已过期，请重新登录')
  localStorage.removeItem('token')
  // 当前已在 /login 则不跳
  if (!window.location.pathname.startsWith('/login')) {
    const redirect = encodeURIComponent(window.location.pathname + window.location.search)
    window.location.href = `/login?redirect=${redirect}`
  }
}

// 响应拦截器 - 统一处理后端 { code, message, data } 格式
request.interceptors.response.use(
  (response) => {
    const res = response.data
    if (res.code === 200) {
      return res.data
    }
    if (res.code === 401) {
      handleUnauthorized(res.message)
      return Promise.reject(new Error(res.message || '未登录'))
    }
    const msg = res.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(new Error(msg))
  },
  (error) => {
    let msg = '网络异常，请稍后重试'
    if (error.code === 'ECONNABORTED') {
      msg = '请求超时，请检查网络连接'
    } else if (error.response) {
      const status = error.response.status
      if (status === 401) {
        handleUnauthorized(error.response.data?.message)
        return Promise.reject(error)
      }
      if (status === 403) {
        ElMessage.error(error.response.data?.message || '权限不足')
        return Promise.reject(error)
      }
      const map = { 400: '请求参数错误', 404: '接口不存在', 500: '服务器内部错误', 502: '后端服务未启动', 503: '服务暂时不可用' }
      msg = map[status] || `服务异常 (${status})`
    } else if (!error.response) {
      msg = '无法连接后端服务，请确认 Flask 已启动'
    }
    ElMessage.error(msg)
    console.error('[API Error]', error.message)
    return Promise.reject(error)
  }
)

export default request
