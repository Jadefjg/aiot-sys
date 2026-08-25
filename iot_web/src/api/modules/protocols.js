import api from '../index'

export const getProtocols = () => api.get('/protocols/list')
export const getProtocol = (name) => api.get(`/protocols/${name}`)
