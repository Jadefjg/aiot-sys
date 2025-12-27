import api from '../index'

// 获取用户列表
export const getUsers = (params = {}) => {
  return api.get('/users', { params })
}

// 获取单个用户
export const getUser = (userId) => {
  return api.get(`/users/${userId}`)
}

// 创建用户
export const createUser = (data) => {
  return api.post('/users', data)
}

// 更新用户
export const updateUser = (userId, data) => {
  return api.put(`/users/${userId}`, data)
}

// 更新当前用户
export const updateCurrentUser = (data) => {
  return api.put('/users/me', data)
}

// 获取当前用户
export const getCurrentUser = () => {
  return api.get('/users/me')
}

// 删除用户
export const deleteUser = (userId) => {
  return api.delete(`/users/${userId}`)
}

// 分配角色给用户
export const assignRoles = (userId, roleIds) => {
  return api.post(`/users/${userId}/roles`, { role_ids: roleIds })
}
