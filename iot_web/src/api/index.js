import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { formatApiDetail } from '@/utils/apiHelpers'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  },
  maxRedirects: 5
})

api.interceptors.request.use((config) => {
  if (config.url) {
    const [path, query] = config.url.split('?')
    if (path && !path.endsWith('/') && path.split('/').filter(Boolean).length === 1) {
      config.url = `${path}/${query ? `?${query}` : ''}`
    }
  }
  return config
})

api.interceptors.request.use(
  config => {
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

const isAuthLogin = (config) => (config?.url || '').includes('/auth/login')

api.interceptors.response.use(
  response => response.data,
  error => {
    const { response, config } = error
    if (config?.skipErrorToast) {
      return Promise.reject(error)
    }
    if (response) {
      const detail = formatApiDetail(response.data?.detail)
      switch (response.status) {
        case 401:
          if (isAuthLogin(config)) {
            break
          }
          localStorage.removeItem('token')
          router.push('/login')
          ElMessage.error('登录已过期，请重新登录')
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error(detail === '请求失败' ? '请求的资源不存在' : detail)
          break
        case 504:
          ElMessage.error(detail === '请求失败' ? '设备响应超时' : detail)
          break
        case 503:
          ElMessage.error(detail === '请求失败' ? '服务暂不可用' : detail)
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(detail)
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default api
