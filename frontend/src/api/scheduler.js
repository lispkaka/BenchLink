import api from './index'

export const getSchedules = (params = {}) => {
  return api.get('/scheduler/schedules/', { params })
}

export const getSchedule = (id) => {
  return api.get(`/scheduler/schedules/${id}/`)
}

export const createSchedule = (data) => {
  const payload = {
    ...data,
    // 后端要求的写入字段
    project_id: data.project || data.project_id,
    testsuite_id: data.testsuite || data.testsuite_id
  }
  delete payload.project
  delete payload.testsuite
  return api.post('/scheduler/schedules/', payload)
}

export const updateSchedule = (id, data) => {
  const payload = {
    ...data,
    project_id: data.project || data.project_id,
    testsuite_id: data.testsuite || data.testsuite_id
  }
  delete payload.project
  delete payload.testsuite
  return api.patch(`/scheduler/schedules/${id}/`, payload)
}

export const deleteSchedule = (id) => {
  return api.delete(`/scheduler/schedules/${id}/`)
}

export const toggleSchedule = (id, status) => {
  return api.patch(`/scheduler/schedules/${id}/`, { status })
}


