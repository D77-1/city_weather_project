import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api'

export const useUserStore = defineStore('user', () => {
  // ========== State ==========
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  // ========== Actions ==========
  async function login(username, password) {
    const data = await request.post('/auth/login', { username, password })
    token.value = data.token
    userInfo.value = data.user
    localStorage.setItem('token', data.token)
    return data.user
  }

  async function fetchMe() {
    if (!token.value) return null
    try {
      const data = await request.get('/auth/me')
      userInfo.value = data
      return data
    } catch (e) {
      // 401 由 axios 拦截器统一处理
      userInfo.value = null
      return null
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return {
    userInfo, token, isLoggedIn, isAdmin,
    login, fetchMe, logout,
  }
})
