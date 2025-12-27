import { defineStore } from 'pinia'
import { login as loginApi, getCurrentUser } from '@/api/modules/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: null,
    loading: false
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isSuperuser: (state) => state.user?.is_superuser || false,
    username: (state) => state.user?.username || ''
  },

  actions: {
    async login(username, password) {
      this.loading = true
      try {
        const response = await loginApi(username, password)
        this.token = response.access_token
        localStorage.setItem('token', response.access_token)
        await this.fetchUser()
        return true
      } catch (error) {
        console.error('登录失败:', error)
        return false
      } finally {
        this.loading = false
      }
    },

    async fetchUser() {
      if (!this.token) return
      try {
        this.user = await getCurrentUser()
      } catch (error) {
        console.error('获取用户信息失败:', error)
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    }
  }
})
