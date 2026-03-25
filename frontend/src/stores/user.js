import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/api'

export const useUserStore = defineStore('user', () => {
  // ========== State ==========
  const userInfo = ref(null)
  const token = ref(localStorage.getItem('token') || '')
  const isLoggedIn = ref(!!token.value)

  // ========== Actions ==========
  async function login(username, password) {
    const data = await request.post('/auth/login', { username, password })
    token.value = data.token
    userInfo.value = data.user
    isLoggedIn.value = true
    localStorage.setItem('token', data.token)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    isLoggedIn.value = false
    localStorage.removeItem('token')
  }

  return {
    userInfo, token, isLoggedIn,
    login, logout,
  }
})
