import api from '../index'

export const getLinks = (params = {}) => api.get('/links', { params })
export const createLink = (data) => api.post('/links', data)
export const updateLink = (linkId, data) => api.put(`/links/${linkId}`, data)
export const deleteLink = (linkId) => api.delete(`/links/${linkId}`)
export const openLink = (linkId, data = {}) => api.post(`/links/${linkId}/open`, data)
export const closeLink = (linkId) => api.post(`/links/${linkId}/close`)
