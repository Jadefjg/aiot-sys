import api from '../index'

// 获取固件列表
export const getFirmwares = (params = {}) => {
  return api.get('/firmware', { params })
}

// 获取单个固件
export const getFirmware = (firmwareId) => {
  return api.get(`/firmware/${firmwareId}`)
}

// 上传固件
export const uploadFirmware = (formData) => {
  return api.post('/firmware/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// 更新固件
export const updateFirmware = (firmwareId, data) => {
  return api.put(`/firmware/${firmwareId}`, null, { params: data })
}

// 删除固件
export const deleteFirmware = (firmwareId) => {
  return api.delete(`/firmware/${firmwareId}`)
}

// 激活固件
export const activateFirmware = (firmwareId) => {
  return api.put(`/firmware/${firmwareId}/activate`)
}

// 获取产品最新固件
export const getLatestFirmware = (productId) => {
  return api.get(`/firmware/product/${productId}/latest`)
}

// 获取升级任务列表
export const getUpgradeTasks = (params = {}) => {
  return api.get('/firmware/tasks', { params })
}

// 获取单个升级任务
export const getUpgradeTask = (taskId) => {
  return api.get(`/firmware/tasks/${taskId}`)
}

// 创建升级任务
export const createUpgradeTask = (data) => {
  return api.post('/firmware/tasks', data)
}

// 取消升级任务
export const cancelUpgradeTask = (taskId) => {
  return api.post(`/firmware/tasks/${taskId}/cancel`)
}

// 删除升级任务
export const deleteUpgradeTask = (taskId) => {
  return api.delete(`/firmware/tasks/${taskId}`)
}
