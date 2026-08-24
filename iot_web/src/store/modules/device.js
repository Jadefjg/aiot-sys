import { defineStore } from 'pinia'
import {
  getDevices,
  getDevice,
  createDevice,
  updateDevice,
  deleteDevice,
  getOnlineDevices
} from '@/api/modules/devices'

export const useDeviceStore = defineStore('device', {
  state: () => ({
    devices: [],
    currentDevice: null,
    onlineDevices: [],
    loading: false,
    total: 0
  }),

  getters: {
    onlineCount: (state) => state.onlineDevices.length,
    offlineCount: (state) => state.devices.filter(d => d.status !== 'online').length
  },

  actions: {
    async fetchDevices(params = {}) {
      this.loading = true
      try {
        this.devices = await getDevices(params)
        this.total = this.devices.length
      } catch (error) {
        console.error('获取设备列表失败:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchDevice(deviceId) {
      try {
        this.currentDevice = await getDevice(deviceId)
      } catch (error) {
        console.error('获取设备详情失败:', error)
      }
    },

    async fetchOnlineDevices() {
      try {
        this.onlineDevices = await getOnlineDevices()
      } catch (error) {
        console.error('获取在线设备失败:', error)
      }
    },

    async addDevice(data) {
      try {
        const device = await createDevice(data)
        this.devices.unshift(device)
        return device
      } catch (error) {
        console.error('创建设备失败:', error)
        throw error
      }
    },

    async editDevice(deviceId, data) {
      try {
        const device = await updateDevice(deviceId, data)
        const index = this.devices.findIndex(d => d.device_id === deviceId)
        if (index !== -1) {
          this.devices[index] = device
        }
        return device
      } catch (error) {
        console.error('更新设备失败:', error)
        throw error
      }
    },

    async removeDevice(deviceId) {
      try {
        await deleteDevice(deviceId)
        this.devices = this.devices.filter(d => d.device_id !== deviceId)
      } catch (error) {
        console.error('删除设备失败:', error)
        throw error
      }
    }
  }
})
