import api from '../index'

// 获取设备列表
export const getDevices = (params = {}) => {
  return api.get('/devices', { params })
}

// 获取单个设备
export const getDevice = (deviceId) => {
  return api.get(`/devices/${deviceId}`)
}

// 创建设备
export const createDevice = (data) => {
  return api.post('/devices', data)
}

// 更新设备
export const updateDevice = (deviceId, data) => {
  return api.put(`/devices/${deviceId}`, data)
}

// 删除设备
export const deleteDevice = (deviceId) => {
  return api.delete(`/devices/${deviceId}`)
}

// 获取在线设备
export const getOnlineDevices = () => {
  return api.get('/devices/status/online')
}

// 获取设备数据
export const getDeviceData = (deviceId, params = {}) => {
  return api.get(`/devices/${deviceId}/data`, { params })
}

// 创建设备数据
export const createDeviceData = (deviceId, data) => {
  return api.post(`/devices/${deviceId}/data`, data)
}

// 发送设备命令
export const sendDeviceCommand = (deviceId, command) => {
  return api.post(`/devices/${deviceId}/commands`, command)
}

// 发送设备控制指令
export const controlDevice = (deviceId, command) => {
  return api.post(`/devices/${deviceId}/control`, command)
}

// 发送命令（别名）
export const sendCommand = (deviceId, command) => {
  return api.post(`/devices/${deviceId}/commands`, command)
}
