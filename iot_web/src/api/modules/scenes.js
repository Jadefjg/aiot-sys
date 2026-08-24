import api from '../index'

export const getGroups = (params = {}) => api.get('/groups', { params })
export const createGroup = (data) => api.post('/groups', data)
export const updateGroup = (id, data) => api.put(`/groups/${id}`, data)
export const deleteGroup = (id) => api.delete(`/groups/${id}`)

export const getScenes = (params = {}) => api.get('/scenes', { params })
export const createScene = (data) => api.post('/scenes', data)
export const updateScene = (id, data) => api.put(`/scenes/${id}`, data)
export const deleteScene = (id) => api.delete(`/scenes/${id}`)

export const getJobs = (params = {}) => api.get('/jobs', { params })
export const createJob = (data) => api.post('/jobs', data)
export const updateJob = (id, data) => api.put(`/jobs/${id}`, data)
export const deleteJob = (id) => api.delete(`/jobs/${id}`)
