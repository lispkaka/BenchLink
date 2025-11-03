import api from './index'

export const getEnvironments = (params = {}) => {
  return api.get('/environments/environments/', { params })
}

export const getEnvironment = (id) => {
  return api.get(`/environments/environments/${id}/`)
}

export const createEnvironment = (data) => {
  return api.post('/environments/environments/', data)
}

export const updateEnvironment = (id, data) => {
  return api.patch(`/environments/environments/${id}/`, data)
}

export const deleteEnvironment = (id) => {
  return api.delete(`/environments/environments/${id}/`)
}

