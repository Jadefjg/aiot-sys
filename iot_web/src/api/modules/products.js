import api from '../index'

export const getProducts = (params = {}) => api.get('/products', { params })
export const getProduct = (productId) => api.get(`/products/${productId}`)
export const createProduct = (data) => api.post('/products', data)
export const updateProduct = (productId, data) => api.put(`/products/${productId}`, data)
export const updateThingModel = (productId, model) =>
  api.put(`/products/${productId}/model`, model)
export const deleteProduct = (productId) => api.delete(`/products/${productId}`)
