import api from '../index'

// 获取权限列表
export const getPermissions = (params = {}) => {
  return api.get('/permissions', { params })
}

// 获取单个权限
export const getPermission = (permissionId) => {
  return api.get(`/permissions/${permissionId}`)
}

// 创建权限
export const createPermission = (data) => {
  return api.post('/permissions', data)
}

// 更新权限
export const updatePermission = (permissionId, data) => {
  return api.put(`/permissions/${permissionId}`, data)
}

// 删除权限
export const deletePermission = (permissionId) => {
  return api.delete(`/permissions/${permissionId}`)
}

// 按资源获取权限
export const getPermissionsByResource = (resource) => {
  return api.get(`/permissions/resource/${resource}`)
}

// 按操作获取权限
export const getPermissionsByAction = (action) => {
  return api.get(`/permissions/action/${action}`)
}
