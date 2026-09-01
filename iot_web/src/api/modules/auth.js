/**
 * 认证 API
 * 登录使用原生 fetch，避免 axios 默认 JSON Content-Type / 拦截器干扰导致 401
 * 其余接口用静态 import，避免登录后动态加载过期 chunk 失败
 */
import api from '../index'

export const login = async (username, password) => {
  const body = new URLSearchParams()
  body.set('username', String(username || '').trim())
  body.set('password', String(password || ''))

  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: body.toString(),
    credentials: 'same-origin',
    cache: 'no-store',
  })

  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const error = new Error(
      (data && (data.detail || data.message)) || `Login failed (${response.status})`
    )
    error.response = { status: response.status, data }
    throw error
  }

  return data
}

export const testToken = () => api.post('/auth/test-token')

export const getCurrentUser = () => api.get('/users/me')

export const register = async (payload) => {
  const response = await fetch('/api/v1/auth/register', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username: String(payload?.username || '').trim(),
      email: payload?.email || undefined,
      password: String(payload?.password || ''),
    }),
    credentials: 'same-origin',
    cache: 'no-store',
  })

  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const error = new Error(
      (data && (data.detail || data.message)) || `Register failed (${response.status})`
    )
    error.response = { status: response.status, data }
    throw error
  }

  return data
}
