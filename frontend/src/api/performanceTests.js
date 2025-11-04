import api from './index'

export const getPerformanceTests = (params = {}) => {
  return api.get('/testcases/performance-tests/', { params })
}

export const getPerformanceTest = (id) => {
  return api.get(`/testcases/performance-tests/${id}/`)
}

export const createPerformanceTest = (data) => {
  return api.post('/testcases/performance-tests/', data)
}

export const updatePerformanceTest = (id, data) => {
  return api.patch(`/testcases/performance-tests/${id}/`, data)
}

export const deletePerformanceTest = (id) => {
  return api.delete(`/testcases/performance-tests/${id}/`)
}

export const executePerformanceTest = (id) => {
  // 性能测试可能需要很长时间（60秒+），需要增加超时时间
  // 使用自定义配置覆盖默认的10秒超时
  return api.post(`/testcases/performance-tests/${id}/execute/`, {}, {
    timeout: 300000  // 5分钟超时（300秒），足够60秒测试 + 启动时间 + 缓冲
  })
}

