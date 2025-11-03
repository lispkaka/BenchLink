import api from './index'

// 获取测试用例列表
export const getTestCases = (params = {}) => {
  return api.get('/testcases/testcases/', { params })
}

// 获取单个测试用例
export const getTestCase = (id) => {
  return api.get(`/testcases/testcases/${id}/`)
}

// 创建测试用例
export const createTestCase = (data) => {
  return api.post('/testcases/testcases/', data)
}

// 更新测试用例
export const updateTestCase = (id, data) => {
  return api.patch(`/testcases/testcases/${id}/`, data)
}

// 删除测试用例
export const deleteTestCase = (id) => {
  return api.delete(`/testcases/testcases/${id}/`)
}

// 执行测试用例
export const executeTestCase = (id, data = {}) => {
  return api.post(`/testcases/testcases/${id}/execute/`, data)
}

// 获取测试用例统计数据
export const getTestCaseStatistics = () => {
  return api.get('/testcases/testcases/statistics/')
}

