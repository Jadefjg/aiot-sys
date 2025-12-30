import { defineStore } from 'pinia'
import { getUsers, getUser, createUser, updateUser } from '@/api/modules/users'

export const useUserStore = defineStore('user', {
  state: () => ({
    users: [],
    currentUser: null,
    loading: false,
    total: 0
  }),

  actions: {
    async fetchUsers(params = {}) {
      this.loading = true
      try {
        this.users = await getUsers(params)
        this.total = this.users.length
      } catch (error) {
        console.error('获取用户列表失败:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchUser(userId) {
      try {
        this.currentUser = await getUser(userId)
      } catch (error) {
        console.error('获取用户详情失败:', error)
      }
    },

    async addUser(data) {
      try {
        const user = await createUser(data)
        this.users.unshift(user)
        return user
      } catch (error) {
        console.error('创建用户失败:', error)
        throw error
      }
    },

    async editUser(userId, data) {
      try {
        const user = await updateUser(userId, data)
        const index = this.users.findIndex(u => u.id === userId)
        if (index !== -1) {
          this.users[index] = user
        }
        return user
      } catch (error) {
        console.error('更新用户失败:', error)
        throw error
      }
    }
  }
})
