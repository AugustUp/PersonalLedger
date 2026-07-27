import axios, { AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

// Unified response envelope (manual 8.2): { code, message, data, request_id }
export interface ApiResult<T = any> {
  code: number
  message: string
  data: T
  request_id: string
}

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  paramsSerializer: (params) => {
    const usp = new URLSearchParams()
    Object.entries(params || {}).forEach(([k, v]) => {
      if (Array.isArray(v)) {
        v.forEach((item) => usp.append(k, String(item)))
      } else if (v !== null && v !== undefined) {
        usp.append(k, String(v))
      }
    })
    return usp.toString()
  },
})

http.interceptors.request.use((config) => {
  const token = useUserStore().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data as ApiResult
    if (res && typeof res.code === 'number' && res.code !== 0) {
      if (res.code === 40101 || res.code === 40100 || res.code === 40199) {
        const user = useUserStore()
        user.logout()
        ElMessage.error(res.message || '登录已过期，请重新登录')
        window.location.href = '/login'
      } else {
        ElMessage.error(res.message || '请求失败')
      }
      return Promise.reject(res)
    }
    return response
  },
  (error) => {
    const res = error.response?.data as ApiResult | undefined
    if (res && typeof res.code === 'number') {
      if (res.code === 40101 || res.code === 40100 || res.code === 40199) {
        useUserStore().logout()
        window.location.href = '/login'
      }
      ElMessage.error(res.message || '请求失败')
    } else {
      ElMessage.error('网络错误，请稍后重试')
    }
    return Promise.reject(error)
  },
)

// Convenience helpers returning the `data` field directly.
export async function get<T = any>(url: string, params?: any): Promise<T> {
  const r = await http.get<ApiResult<T>>(url, { params })
  return r.data.data
}
export async function post<T = any>(url: string, body?: any): Promise<T> {
  const r = await http.post<ApiResult<T>>(url, body)
  return r.data.data
}
export async function patch<T = any>(url: string, body?: any): Promise<T> {
  const r = await http.patch<ApiResult<T>>(url, body)
  return r.data.data
}
export async function del<T = any>(url: string): Promise<T> {
  const r = await http.delete<ApiResult<T>>(url)
  return r.data.data
}
export async function upload<T = any>(url: string, formData: FormData): Promise<T> {
  const r = await http.post<ApiResult<T>>(url, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return r.data.data
}

export default http
