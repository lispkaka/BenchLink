import api from './index'

export const getProjects = (params = {}) => {
  return api.get('/projects/projects/', { params })
}

export const getProject = (id) => {
  return api.get(`/projects/projects/${id}/`)
}

export const createProject = (data) => {
  return api.post('/projects/projects/', data)
}

export const updateProject = (id, data) => {
  return api.patch(`/projects/projects/${id}/`, data)
}

export const deleteProject = (id) => {
  return api.delete(`/projects/projects/${id}/`)
}

export const getProjectStatistics = (params = {}) => {
  return api.get('/projects/projects/statistics/', { params })
}


