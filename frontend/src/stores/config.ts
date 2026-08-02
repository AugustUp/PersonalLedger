// 台账定制配置 store：登录后拉取一次；任何缺省都回退内置默认，保证系统照常工作。
import { defineStore } from 'pinia'
import { customizationApi } from '@/api'
import type { CategoryGroup, LedgerCustomization } from '@/api/types'

const DEFAULT_NAMES: Record<string, string> = {
  meetings: '会议调试台账',
  network_assets: 'IP/MAC 台账',
  account_batches: '批量账号台账',
  maintenance: '通用维护台账',
}

const DEFAULT_GROUPS: CategoryGroup[] = [
  { label: '账号类', options: ['OA', '邮箱'] },
  { label: '终端类', options: ['终端正版化', '终端安全软件'] },
  { label: '网络类', options: ['网络维护', 'WIFI', '告警维护', '封禁IP'] },
  { label: '无线类', options: ['ncecampus无线', '深澜无线', 'AC维护AP'] },
]

// 默认字段标签（与后端默认一致，仅用于 store 未加载时的回退）
const DEFAULT_FIELDS: Record<string, Record<string, { label: string }>> = {
  meetings: {
    meeting_name: { label: '会议名称' }, meeting_time: { label: '会议时间' },
    location: { label: '地点' }, contact_name: { label: '联系人' },
    contact_phone: { label: '联系电话' }, technicians: { label: '调试人员' },
    equipment: { label: '设备' }, debug_content: { label: '调试内容' },
    problem_description: { label: '问题' }, handling_process: { label: '处理过程' },
    result: { label: '结果' }, onsite_support: { label: '现场保障' },
    status: { label: '状态' }, remark: { label: '备注' },
  },
  network_assets: {
    ip_address: { label: 'IP 地址' }, mac_address: { label: 'MAC 地址' },
    user_name: { label: '使用人' }, department: { label: '部门' },
    device_name: { label: '设备名称' }, device_type: { label: '设备类型' },
    building: { label: '楼宇' }, room: { label: '房间' },
    vlan: { label: 'VLAN' }, switch_name: { label: '交换机' },
    switch_port: { label: '端口' }, account_name: { label: '账号名称' },
    registered_at: { label: '登记日期' }, status: { label: '状态' },
    remark: { label: '备注' },
  },
  account_batches: {
    batch_name: { label: '批次名称' }, account_type: { label: '账号类型' },
    applicant_department: { label: '申请部门' }, applicant: { label: '申请人' },
    application_date: { label: '申请日期' }, handler: { label: '经办人' },
    status: { label: '状态' }, remark: { label: '备注' },
  },
  maintenance: {
    category: { label: '分类' }, related_system: { label: '关联系统/设备' },
    requester: { label: '报修人' }, department: { label: '部门' },
    contact_phone: { label: '联系电话' }, location: { label: '地点' },
    problem_description: { label: '问题描述' }, handling_process: { label: '处理过程' },
    fault_cause: { label: '故障原因' }, result: { label: '处理结果' },
    status: { label: '状态' }, handler: { label: '经办人' },
    started_at: { label: '开始时间' }, finished_at: { label: '结束时间' },
    remark: { label: '备注' },
  },
}

export const useConfigStore = defineStore('config', {
  state: () => ({
    config: null as LedgerCustomization | null,
    loaded: false,
  }),
  getters: {
    ledgerName: (s) => (key: string) =>
      s.config?.ledger_names?.[key] || DEFAULT_NAMES[key] || key,
    categoryGroups: (s) => (): CategoryGroup[] =>
      s.config?.maintenance_categories?.length ? s.config.maintenance_categories : DEFAULT_GROUPS,
    fieldLabel: (s) => (module: string, field: string) =>
      s.config?.field_meta?.[module]?.[field]?.label || DEFAULT_FIELDS[module]?.[field]?.label || field,
    // 由分类反查业务分组（用于导航高亮、列表范围）
    categoryGroupOf: (s) => (cat: string) => {
      const groups = s.config?.maintenance_categories?.length ? s.config.maintenance_categories : DEFAULT_GROUPS
      const g = groups.find((x) => x.options.includes(cat))
      return g ? g.label : (groups[0]?.label || '账号类')
    },
  },
  actions: {
    async fetch() {
      if (this.loaded) return
      try {
        this.config = await customizationApi.get()
      } catch {
        /* 拉取失败回退默认 */
      }
      this.loaded = true
    },
    async save(patch: Partial<LedgerCustomization>) {
      this.config = await customizationApi.update(patch)
      return this.config
    },
  },
})
