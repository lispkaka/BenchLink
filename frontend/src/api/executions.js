import api from './index'

export const getExecutions = (params = {}) => {
  return api.get('/executions/executions/', { params })
}

export const getExecution = (id) => {
  return api.get(`/executions/executions/${id}/`)
}

export const deleteExecution = (id) => {
  return api.delete(`/executions/executions/${id}/`)
}

export const batchDeleteExecutions = (ids) => {
  return api.post('/executions/executions/batch_delete/', { ids })
}


