import api from './index'

export const login = (data) => api.post('/users/users/login/', data)
export const register = (data) => api.post('/users/users/register/', data)
export const getCurrentUser = () => api.get('/users/users/me/')



