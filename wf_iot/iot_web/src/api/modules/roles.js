import api from '../index'

// 获取角色列表
export const getRoles = (params = {}) => {
  return api.get('/roles', { params })
}

// 获取单个角色
export const getRole = (roleId) => {
  return api.get(`/roles/${roleId}`)
}

// 创建角色
export const createRole = (data) => {
  return api.post('/roles', data)
}

// 更新角色
export const updateRole = (roleId, data) => {
  return api.put(`/roles/${roleId}`, data)
}

// 删除角色
export const deleteRole = (roleId) => {
  return api.delete(`/roles/${roleId}`)
}

// 获取角色权限
export const getRolePermissions = (roleId) => {
  return api.get(`/roles/${roleId}/permissions`)
}

// 分配权限给角色
export const assignPermission = (roleId, permissionId) => {
  return api.post(`/roles/${roleId}/permissions/${permissionId}`)
}

// 移除角色权限
export const removePermission = (roleId, permissionId) => {
  return api.delete(`/roles/${roleId}/permissions/${permissionId}`)
}

// 批量分配权限给角色
export const assignPermissions = (roleId, permissionIds) => {
  return api.post(`/roles/${roleId}/permissions`, { permission_ids: permissionIds })
}
