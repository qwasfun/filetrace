import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  // 从 localStorage 初始化状态
  const accessToken = ref(localStorage.getItem('access_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // 计算属性：是否已登录
  const isAuthenticated = computed(() => !!accessToken.value)

  // 计算属性：是否为管理员
  const isAdmin = computed(() => user.value?.role === 'admin')

  // 设置认证信息
  const setAuth = (authData) => {
    const { access_token, user: userData } = authData

    accessToken.value = access_token
    user.value = userData

    // 同步到 localStorage
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  // 清除认证信息
  const clearAuth = () => {
    accessToken.value = null
    user.value = null

    // 从 localStorage 移除
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  // 更新 access token
  const updateAccessToken = (token) => {
    accessToken.value = token
    localStorage.setItem('access_token', token)
  }

  return {
    accessToken,
    user,
    isAuthenticated,
    isAdmin,
    setAuth,
    clearAuth,
    updateAccessToken,
  }
})
