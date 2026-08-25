import { defineStore } from 'pinia'
import { login as loginApi, getCurrentUser } from '@/api/modules/auth'

function readCachedUser() {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: readCachedUser(),
    permissions: [],
    loading: false,
    access: { is_superuser: false, products: {}, devices: {} }
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isSuperuser: (state) => state.user?.is_superuser || false,
    hasPermission: (state) => (code) =>
      state.user?.is_superuser || state.permissions.includes('*') || state.permissions.includes(code),
    username: (state) => state.user?.username || '',
    productRole: (state) => (productId) => {
      if (state.user?.is_superuser) return 'admin'
      return state.access?.products?.[productId] || null
    },
    deviceRole: (state) => (deviceId, productId) => {
      if (state.user?.is_superuser) return 'admin'
      return state.access?.devices?.[deviceId] || state.access?.products?.[productId] || null
    }
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
        const status = error.response?.status
        // 401 才视为凭证错误；404/5xx 由全局拦截器提示
        if (status === 401) {
          return false
        }
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchUser() {
      if (!this.token) return
      try {
        const { getMyPermissions } = await import('@/api/modules/users')
        const [user, permRes] = await Promise.all([getCurrentUser(), getMyPermissions()])
        this.user = user
        this.permissions = permRes?.permissions || []
        localStorage.setItem('user', JSON.stringify(this.user))
        await this.fetchAccess()
      } catch (error) {
        console.error('获取用户信息失败:', error)
        this.logout()
      }
    },

    async fetchAccess() {
      if (!this.token) return
      try {
        const { getMyAccess } = await import('@/api/modules/acl')
        this.access = await getMyAccess()
      } catch {
        this.access = { is_superuser: this.isSuperuser, products: {}, devices: {} }
      }
    },

    logout() {
      this.token = null
      this.user = null
      this.permissions = []
      this.access = { is_superuser: false, products: {}, devices: {} }
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
