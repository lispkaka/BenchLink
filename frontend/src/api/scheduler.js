import api from './index'

export const getSchedules = (params = {}) => {
  return api.get('/scheduler/schedules/', { params })
}

export const getSchedule = (id) => {
  return api.get(`/scheduler/schedules/${id}/`)
}

export const createSchedule = (data) => {
  return api.post('/scheduler/schedules/', data)
}

export const updateSchedule = (id, data) => {
  return api.patch(`/scheduler/schedules/${id}/`, data)
}

export const deleteSchedule = (id) => {
  return api.delete(`/scheduler/schedules/${id}/`)
}

export const toggleSchedule = (id, status) => {
  return api.patch(`/scheduler/schedules/${id}/`, { status })
}


