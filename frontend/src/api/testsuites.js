import api from './index'

export const getTestSuites = (params = {}) => {
  return api.get('/testsuites/testsuites/', { params })
}

export const getTestSuite = (id) => {
  return api.get(`/testsuites/testsuites/${id}/`)
}

export const createTestSuite = (data) => {
  return api.post('/testsuites/testsuites/', data)
}

export const updateTestSuite = (id, data) => {
  return api.patch(`/testsuites/testsuites/${id}/`, data)
}

export const deleteTestSuite = (id) => {
  return api.delete(`/testsuites/testsuites/${id}/`)
}

export const executeTestSuite = (id) => {
  return api.post(`/testsuites/testsuites/${id}/execute/`)
}

export const reorderTestCases = (id, testcase_orders) => {
  return api.post(`/testsuites/testsuites/${id}/reorder_testcases/`, { testcase_orders })
}


