import api from '../index'

const pid = (productId) => encodeURIComponent(productId)

export const getProducts = (params = {}) => api.get('/products', { params })
export const getProduct = (productId) => api.get(`/products/${pid(productId)}`)
export const createProduct = (data) => api.post('/products', data)
export const updateProduct = (productId, data) => api.put(`/products/${pid(productId)}`, data)
export const updateThingModel = (productId, model) =>
  api.put(`/products/${pid(productId)}/model`, model)
export const updateProductConfig = (productId, name, config) =>
  api.put(`/products/${pid(productId)}/config/${encodeURIComponent(name)}`, config)
export const bindProductChannels = (productId, data) =>
  api.put(`/products/${pid(productId)}/channels`, data)
export const deleteProduct = (productId) => api.delete(`/products/${pid(productId)}`)
