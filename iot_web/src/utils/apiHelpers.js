export const unwrapList = (data, key) => {
  if (Array.isArray(data)) return data
  if (data && key && Array.isArray(data[key])) return data[key]
  return []
}

export const formatApiDetail = (detail) => {
  if (!detail) return '请求失败'
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item.message || JSON.stringify(item)).join('; ')
  }
  if (typeof detail === 'object') {
    return detail.msg || detail.message || detail.detail || JSON.stringify(detail)
  }
  return String(detail)
}
