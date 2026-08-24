import api from '../index'

export const getAlarms = (params = {}) => api.get('/alarms', { params })
export const acknowledgeAlarm = (alarmId) =>
  api.post(`/alarms/${alarmId}/acknowledge`)
