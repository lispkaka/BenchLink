import api from './index'

export const getGlobalTokens = (params = {}) => {
  return api.get('/environments/global-tokens/', { params })
}

export const getGlobalToken = (id) => {
  return api.get(`/environments/global-tokens/${id}/`)
}

export const createGlobalToken = (data) => {
  return api.post('/environments/global-tokens/', data)
}

export const updateGlobalToken = (id, data) => {
  return api.patch(`/environments/global-tokens/${id}/`, data)
}

export const deleteGlobalToken = (id) => {
  return api.delete(`/environments/global-tokens/${id}/`)
}

