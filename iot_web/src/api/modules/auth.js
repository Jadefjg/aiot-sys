import api from '../index'

// 登录
export const login = (username, password) => {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)
  return api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

// 测试token
export const testToken = () => {
  return api.post('/auth/test-token')
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return api.get('/users/me')
}
