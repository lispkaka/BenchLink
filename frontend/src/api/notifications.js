import api from './index'

/**
 * 获取通知渠道列表
 */
export const getNotificationChannels = (params = {}) => {
  return api.get('/notifications/channels/', { params })
}

/**
 * 创建通知渠道
 */
export const createNotificationChannel = (data) => {
  return api.post('/notifications/channels/', data)
}

/**
 * 获取单个通知渠道
 */
export const getNotificationChannel = (id) => {
  return api.get(`/notifications/channels/${id}/`)
}

/**
 * 更新通知渠道
 */
export const updateNotificationChannel = (id, data) => {
  return api.patch(`/notifications/channels/${id}/`, data)
}

/**
 * 删除通知渠道
 */
export const deleteNotificationChannel = (id) => {
  return api.delete(`/notifications/channels/${id}/`)
}

/**
 * 测试通知渠道
 */
export const testNotificationChannel = (id) => {
  return api.post(`/notifications/channels/${id}/test/`)
}



