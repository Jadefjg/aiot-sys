import api from '../index'

export const getMyAccess = () => api.get('/acl/me')
export const getAclUsers = () => api.get('/acl/users')
export const getProductAcl = (productId) => api.get(`/acl/products/${encodeURIComponent(productId)}`)
export const grantProductAcl = (productId, data) =>
  api.post(`/acl/products/${encodeURIComponent(productId)}`, data)
export const revokeProductAcl = (productId, userId) =>
  api.delete(`/acl/products/${encodeURIComponent(productId)}/${userId}`)
export const getDeviceAcl = (deviceId) => api.get(`/acl/devices/${encodeURIComponent(deviceId)}`)
export const grantDeviceAcl = (deviceId, data) =>
  api.post(`/acl/devices/${encodeURIComponent(deviceId)}`, data)
export const revokeDeviceAcl = (deviceId, userId) =>
  api.delete(`/acl/devices/${encodeURIComponent(deviceId)}/${userId}`)
