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

export const getBindings = (params = {}) => api.get('/bindings', { params })
export const createBinding = (data) => api.post('/bindings', data)
export const updateBinding = (id, data) => api.put(`/bindings/${id}`, data)
export const deleteBinding = (id) => api.delete(`/bindings/${id}`)

export const getScripts = (params = {}) => api.get('/scripts', { params })
export const createScript = (data) => api.post('/scripts', data)
export const updateScript = (id, data) => api.put(`/scripts/${id}`, data)
export const deleteScript = (id) => api.delete(`/scripts/${id}`)
export const runScript = (id, data = {}) => api.post(`/scripts/${id}/run`, data)
export const previewScript = (data) => api.post('/scripts/preview', data)
