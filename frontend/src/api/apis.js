import api from './index'

export const getAPIs = (params = {}) => {
  return api.get('/apis/apis/', { params })
}

export const getAPI = (id) => {
  return api.get(`/apis/apis/${id}/`)
}

export const createAPI = (data) => {
  return api.post('/apis/apis/', data)
}

export const updateAPI = (id, data) => {
  return api.patch(`/apis/apis/${id}/`, data)
}

export const deleteAPI = (id) => {
  return api.delete(`/apis/apis/${id}/`)
}

export const executeAPI = (id, data = {}) => {
  return api.post(`/apis/apis/${id}/execute/`, data)
}


