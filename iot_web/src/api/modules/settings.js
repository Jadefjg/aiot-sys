import api from '../index'

export const getSettingModules = () => api.get('/settings/')
export const getSettingForm = (module) => api.get(`/settings/${module}/form`)
export const getSettingValues = (module) => api.get(`/settings/${module}`)
export const saveSettingValues = (module, values) => api.post(`/settings/${module}`, values)
