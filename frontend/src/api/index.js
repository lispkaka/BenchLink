import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('token')
      if (token && token.trim()) {
        // Django REST Framework TokenAuthentication 格式: Token <token>
        config.headers.Authorization = `Token ${token.trim()}`
        // 开发环境下打印调试信息
        if (import.meta.env.DEV) {
          console.log('[API Request]', config.method?.toUpperCase(), config.url, 'Token:', token.substring(0, 10) + '...')
        }
      } else {
        // 如果没有 token，在开发环境下警告
        if (import.meta.env.DEV && !config.url?.includes('/login') && !config.url?.includes('/register')) {
          console.warn('[API Request] No token found for:', config.method?.toUpperCase(), config.url)
        }
      }
    }
    return config
  },
  error => {
    console.error('[API Request Error]', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api



