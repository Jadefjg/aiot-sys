import api from '../index'

export const getChannels = (params = {}) => api.get('/channels', { params })
export const createChannel = (data) => api.post('/channels', data)
export const updateChannel = (id, data) => api.put(`/channels/${id}`, data)
export const deleteChannel = (id) => api.delete(`/channels/${id}`)
export const enableChannel = (id) => api.post(`/channels/${id}/enable`)
export const disableChannel = (id) => api.post(`/channels/${id}/disable`)
export const getChannelLogs = (id) => api.get(`/channels/${id}/logs`)
export const ingestChannel = (id, data) => api.post(`/channels/${id}/ingest`, data)

export const getRules = (params = {}) => api.get('/rules', { params })
export const createRule = (data) => api.post('/rules', data)
export const updateRule = (id, data) => api.put(`/rules/${id}`, data)
export const deleteRule = (id) => api.delete(`/rules/${id}`)
