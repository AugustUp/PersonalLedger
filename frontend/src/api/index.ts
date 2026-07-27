// Centralized API client. Every function returns the backend `data` field
// (see http.ts). Export endpoints are binary downloads handled by `download`.
import { ElMessage } from 'element-plus'
import { get, post, patch, del, upload } from './http'
import { useUserStore } from '@/stores/user'
import type {
  AccountBatchDetail,
  AccountBatchItem,
  AccountBatchListItem,
  Attachment,
  DashboardSummary,
  DepartmentOut,
  ImportPreview,
  MaintenanceDetail,
  MaintenanceListItem,
  MeetingDetail,
  MeetingListItem,
  NetworkAssetDetail,
  NetworkAssetHistory,
  NetworkAssetListItem,
  OperationLog,
  PageResult,
  UserMe,
  UserOut,
} from './types'

function clean(obj: Record<string, any>): Record<string, any> {
  const r: Record<string, any> = {}
  for (const k of Object.keys(obj)) {
    const v = obj[k]
    if (v !== null && v !== undefined && v !== '') r[k] = v
  }
  return r
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export const authApi = {
  login: (username: string, password: string) =>
    post<{ access_token: string; token_type: string; expires_in: number }>('/auth/login', {
      username,
      password,
    }),
  me: () => get<UserMe>('/auth/me'),
  logout: () => post('/auth/logout', {}),
}

// ---------------------------------------------------------------------------
// Departments
// ---------------------------------------------------------------------------
export const departmentApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string } = {}) =>
    get<PageResult<DepartmentOut>>('/departments', clean(params)),
  create: (body: Partial<DepartmentOut> & { name: string }) => post<DepartmentOut>('/departments', body),
  update: (id: number, body: Partial<DepartmentOut>) => patch<DepartmentOut>(`/departments/${id}`, body),
  remove: (id: number) => del(`/departments/${id}`),
}

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------
export const userApi = {
  list: (params: { page?: number; page_size?: number; keyword?: string } = {}) =>
    get<PageResult<UserOut>>('/users', clean(params)),
  create: (body: {
    username: string
    password: string
    real_name: string
    role: string
    department_id?: number | null
    is_active?: boolean
  }) => post<UserOut>('/users', body),
  update: (
    id: number,
    body: { real_name?: string; role?: string; department_id?: number | null; is_active?: boolean },
  ) => patch<UserOut>(`/users/${id}`, body),
  resetPassword: (id: number, new_password: string) =>
    post(`/users/${id}/reset-password`, { new_password }),
}

// ---------------------------------------------------------------------------
// Meetings
// ---------------------------------------------------------------------------
export const meetingApi = {
  list: (params: Record<string, any>) => get<PageResult<MeetingListItem>>('/meetings', clean(params)),
  get: (id: number) => get<MeetingDetail>(`/meetings/${id}`),
  create: (body: Record<string, any>) => post<MeetingDetail>('/meetings', body),
  update: (id: number, body: Record<string, any>) => patch<MeetingDetail>(`/meetings/${id}`, body),
  remove: (id: number) => del(`/meetings/${id}`),
  restore: (id: number) => post<MeetingDetail>(`/meetings/${id}/restore`, {}),
}

// ---------------------------------------------------------------------------
// Network assets
// ---------------------------------------------------------------------------
export const networkAssetApi = {
  list: (params: Record<string, any>) =>
    get<PageResult<NetworkAssetListItem>>('/network-assets', clean(params)),
  get: (id: number) => get<NetworkAssetDetail>(`/network-assets/${id}`),
  create: (body: Record<string, any>) => post<NetworkAssetDetail>('/network-assets', body),
  update: (id: number, body: Record<string, any>) => patch<NetworkAssetDetail>(`/network-assets/${id}`, body),
  histories: (id: number) => get<NetworkAssetHistory[]>(`/network-assets/${id}/histories`),
  importPreview: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return upload<ImportPreview>('/network-assets/import/preview', fd)
  },
  importCommit: (import_token: string, strategy: 'skip' | 'update' = 'skip') =>
    post('/network-assets/import/commit', { import_token, strategy }),
}

// ---------------------------------------------------------------------------
// Account batches
// ---------------------------------------------------------------------------
export const accountBatchApi = {
  list: (params: Record<string, any>) =>
    get<PageResult<AccountBatchListItem>>('/account-batches', clean(params)),
  get: (id: number) => get<AccountBatchDetail>(`/account-batches/${id}`),
  create: (body: Record<string, any>) => post<AccountBatchDetail>('/account-batches', body),
  update: (id: number, body: Record<string, any>) => patch<AccountBatchDetail>(`/account-batches/${id}`, body),
  remove: (id: number) => del(`/account-batches/${id}`),
  items: (id: number, params: Record<string, any> = {}) =>
    get<PageResult<AccountBatchItem>>(`/account-batches/${id}/items`, clean(params)),
  importPreview: (id: number, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return upload<ImportPreview>(`/account-batches/${id}/items/import/preview`, fd)
  },
  importCommit: (id: number, import_token: string, strategy: 'skip' | 'update' = 'skip') =>
    post(`/account-batches/${id}/items/import/commit`, { import_token, strategy }),
  batchResult: (id: number, items: { id: number; result: string; failure_reason?: string | null }[]) =>
    patch(`/account-batches/${id}/items/batch`, { items }),
}

// ---------------------------------------------------------------------------
// Maintenance
// ---------------------------------------------------------------------------
export const maintenanceApi = {
  list: (params: Record<string, any>) =>
    get<PageResult<MaintenanceListItem>>('/maintenance-records', clean(params)),
  get: (id: number) => get<MaintenanceDetail>(`/maintenance-records/${id}`),
  create: (body: Record<string, any>) => post<MaintenanceDetail>('/maintenance-records', body),
  update: (id: number, body: Record<string, any>) =>
    patch<MaintenanceDetail>(`/maintenance-records/${id}`, body),
  remove: (id: number) => del(`/maintenance-records/${id}`),
  restore: (id: number) => post<MaintenanceDetail>(`/maintenance-records/${id}/restore`, {}),
}

// ---------------------------------------------------------------------------
// Attachments
// ---------------------------------------------------------------------------
export const attachmentApi = {
  list: (businessType: string, businessId: number) =>
    get<Attachment[]>('/attachments', { business_type: businessType, business_id: businessId }),
  upload: (businessType: string, businessId: number, file: File) => {
    const fd = new FormData()
    fd.append('business_type', businessType)
    fd.append('business_id', String(businessId))
    fd.append('file', file)
    return upload<Attachment>('/attachments', fd)
  },
  remove: (id: number) => del(`/attachments/${id}`),
}

// ---------------------------------------------------------------------------
// Dashboard & logs
// ---------------------------------------------------------------------------
export const dashboardApi = {
  summary: () => get<DashboardSummary>('/dashboard/summary'),
}

export const operationLogApi = {
  list: (params: Record<string, any>) => get<PageResult<OperationLog>>('/operation-logs', clean(params)),
}

// ---------------------------------------------------------------------------
// Export download (binary, needs Authorization header)
// ---------------------------------------------------------------------------
export async function download(url: string, defaultName = 'download.xlsx') {
  const token = useUserStore().token
  const resp = await fetch(`/api/v1${url}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!resp.ok) {
    ElMessage.error('导出失败，请检查权限或重试')
    return
  }
  const blob = await resp.blob()
  const cd = resp.headers.get('content-disposition') || ''
  const m = cd.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)/)
  const name = m ? decodeURIComponent(m[1]) : defaultName
  const a = document.createElement('a')
  const href = URL.createObjectURL(blob)
  a.href = href
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(href)
}
