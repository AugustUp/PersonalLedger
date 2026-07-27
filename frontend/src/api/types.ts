// Shared API types mirroring backend Pydantic schemas (manual 9.4).

export interface PageResult<T> {
  items: T[]
  page: number
  page_size: number
  total: number
  pages: number
}

export interface UserMe {
  id: number
  username: string
  real_name: string
  role: string
  department_id: number | null
  department_name: string | null
  permissions: string[]
}

export interface UserOut {
  id: number
  username: string
  real_name: string
  role: string
  department_id: number | null
  department_name: string | null
  is_active: boolean
  created_at: string | null
  updated_at: string | null
}

export interface DepartmentOut {
  id: number
  name: string
  code: string | null
  parent_id: number | null
  remark: string | null
  user_count: number
}

export interface MeetingListItem {
  id: number
  record_no: string
  meeting_name: string
  meeting_time: string | null
  location: string | null
  contact_name: string | null
  technicians: string | null
  status: string
  onsite_support: boolean
  created_at: string | null
  updated_at: string | null
}
export type MeetingDetail = MeetingListItem & Record<string, any>

export interface NetworkAssetListItem {
  id: number
  ip_address: string | null
  mac_address: string | null
  user_name: string | null
  department_id: number | null
  department_name: string | null
  device_name: string | null
  device_type: string | null
  building: string | null
  room: string | null
  status: string
  registered_at: string | null
  updated_at: string | null
}
export type NetworkAssetDetail = NetworkAssetListItem & Record<string, any>

export interface NetworkAssetHistory {
  id: number
  asset_id: number
  field_name: string
  old_value: string | null
  new_value: string | null
  change_reason: string | null
  changed_by: number | null
  changed_at: string | null
}

export interface AccountBatchListItem {
  id: number
  batch_no: string
  batch_name: string
  account_type: string | null
  applicant: string | null
  applicant_department: string | null
  application_date: string | null
  total_count: number
  success_count: number
  failed_count: number
  pending_count: number
  status: string
  handler: string | null
  created_at: string | null
  updated_at: string | null
}
export type AccountBatchDetail = AccountBatchListItem & Record<string, any>

export interface AccountBatchItem {
  id: number
  batch_id: number
  real_name: string | null
  identity_no: string | null
  department: string | null
  account_name: string | null
  account_type: string | null
  permission_type: string | null
  valid_until: string | null
  result: string
  failure_reason: string | null
  processed_at: string | null
  remark: string | null
}

export interface MaintenanceListItem {
  id: number
  record_no: string
  category: string | null
  related_system: string | null
  requester: string | null
  department_id: number | null
  department_name: string | null
  location: string | null
  status: string
  handler: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string | null
  updated_at: string | null
}
export type MaintenanceDetail = MaintenanceListItem & Record<string, any>

export interface Attachment {
  id: number
  business_type: string
  business_id: number
  original_name: string
  mime_type: string | null
  size: number
  uploaded_by: number | null
  created_at: string | null
}

export interface OperationLog {
  id: number
  user_id: number | null
  module: string
  action: string
  business_id: number | null
  description: string | null
  request_ip: string | null
  created_at: string | null
}

export interface DashboardSummary {
  meeting_total: number
  meeting_pending: number
  network_asset_total: number
  network_asset_active: number
  account_batch_total: number
  account_batch_pending: number
  maintenance_total: number
  maintenance_pending: number
  user_total: number
  recent_maintenance: any[]
  recent_meetings: any[]
}

export interface ImportPreview {
  import_token: string
  total_rows: number
  valid_rows: number
  invalid_rows: number
  errors: { row: number; field: string | null; message: string }[]
  sample: Record<string, any>[]
}

// Status enum maps (manual appendix C)
export const STATUS_LABELS: Record<string, Record<string, string>> = {
  meeting: { pending: '待调试', debugged: '已调试', supporting: '保障中', completed: '已完成', cancelled: '已取消' },
  network_asset: { active: '使用中', inactive: '已停用', replaced: '已更换' },
  account_batch: { draft: '草稿', pending: '待处理', processing: '处理中', partial: '部分完成', completed: '已完成', cancelled: '已取消' },
  account_item: { pending: '待处理', success: '成功', failed: '失败', skipped: '跳过' },
  maintenance: { pending: '待处理', processing: '处理中', resolved: '已解决', unresolved: '未解决', closed: '已关闭' },
}

// 通用维护台账的任务分类（覆盖会议之外的全部运维领域）
export const MAINTENANCE_CATEGORIES: string[] = [
  'OA',
  '邮箱',
  '终端正版化',
  '终端安全软件',
  '网络维护',
  'WIFI',
  '告警维护',
  '封禁IP',
  'ncecampus无线',
  '深澜无线',
  'AC维护AP',
]

// 分类下拉分组（账号类 / 终端类 / 网络类 / 无线类）
export const MAINTENANCE_CATEGORY_GROUPS: { label: string; options: string[] }[] = [
  { label: '账号类', options: ['OA', '邮箱'] },
  { label: '终端类', options: ['终端正版化', '终端安全软件'] },
  { label: '网络类', options: ['网络维护', 'WIFI', '告警维护', '封禁IP'] },
  { label: '无线类', options: ['ncecampus无线', '深澜无线', 'AC维护AP'] },
]

export const CATEGORY_LABELS: Record<string, string> = Object.fromEntries(
  MAINTENANCE_CATEGORIES.map((c) => [c, c]),
)
