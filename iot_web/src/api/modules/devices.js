import api from '../index'

const did = (deviceId) => encodeURIComponent(deviceId)

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

export const getDeviceValues = (deviceId) => api.get(`/devices/${did(deviceId)}/values`)
export const putDeviceValues = (deviceId, values) =>
  api.post(`/devices/${deviceId}/values`, { values })
export const syncDevice = (deviceId) =>
  api.get(`/devices/${deviceId}/sync`, { timeout: 35000 })
export const readDevice = (deviceId, points = []) =>
  api.post(`/devices/${deviceId}/read`, { points }, { timeout: 35000 })
export const writeDevice = (deviceId, values) =>
  api.post(`/devices/${deviceId}/write`, { values }, { timeout: 35000 })
export const invokeAction = (deviceId, action, params = {}) =>
  api.post(`/devices/${deviceId}/action/${action}`, { params }, { timeout: 35000 })
export const pushSetting = (deviceId, name, data) =>
  api.post(`/devices/${deviceId}/setting/${name}`, { data }, { timeout: 35000 })
export const registerDevice = (deviceId, data = {}) =>
  api.post(`/devices/${deviceId}/register`, data)

export const exportDevices = (params = {}) => api.get('/devices/export', { params })
export const importDevices = (devices) => api.post('/devices/import', { devices })
export const getDeviceTrack = (deviceId, params = {}) =>
  api.get(`/devices/${deviceId}/track`, { params })
export const getDeviceHistory = (deviceId, params = {}) =>
  api.get(`/devices/${deviceId}/history`, { params })
export const downloadGatewayConfig = (deviceId, database) =>
  api.get(`/devices/${deviceId}/download/${database}`)
export const getDeviceShadow = (deviceId) => api.get(`/devices/${deviceId}/shadow`)
export const setDeviceShadow = (deviceId, desired) =>
  api.put(`/devices/${deviceId}/shadow`, { desired })
export const meterSwitch = (deviceId, data) =>
  api.post(`/devices/${deviceId}/meter/switch`, data)
