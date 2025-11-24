import api from './index'

// 获取仪表盘统计数据
export const getDashboardData = (params = {}) => {
  return api.get('/executions/executions/dashboard/', { params })
}










