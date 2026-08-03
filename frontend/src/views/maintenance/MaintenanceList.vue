<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { maintenanceApi, departmentApi, download } from '@/api'
import { fmtDateTime, fmtDuration } from '@/utils/format'
import { STATUS_LABELS } from '@/api/types'
import { useConfigStore } from '@/stores/config'
import StatusTag from '@/components/StatusTag.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyHint from '@/components/EmptyHint.vue'
import type { DepartmentOut } from '@/api/types'

const route = useRoute()
const router = useRouter()
const config = useConfigStore()
const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const departments = ref<DepartmentOut[]>([])
const showMore = ref(false)

const filters = reactive({
  keyword: '',
  status: '',
  categories: [] as string[],
  related_system: '',
  handler: '',
  requester: '',
  department_id: null as number | null,
  start_date: '',
  end_date: '',
})
const page = reactive({ page: 1, page_size: 20 })

const statusOptions = Object.entries(STATUS_LABELS.maintenance).map(([v, l]) => ({ value: v, label: l }))
const categoryGroups = computed(() => config.categoryGroups())

// 支持从工作台（?category=）或侧边栏分组导航（?group=）进入时预筛选
function applyQuery() {
  const q = route.query
  const group = typeof q.group === 'string' ? q.group : ''
  const cat = typeof q.category === 'string' ? q.category : ''
  if (group) {
    const g = config.categoryGroups().find((x) => x.label === group)
    filters.categories = g ? [...g.options] : []
  } else if (cat) {
    filters.categories = [cat]
  } else {
    filters.categories = []
  }
  filters.related_system = typeof q.related_system === 'string' ? q.related_system : ''
}

// 当前分组（用于跳转时保持导航高亮连贯）
const currentGroup = computed(() => {
  const g = route.query.group
  return typeof g === 'string' && g ? g : (filters.categories.length === 1 ? config.categoryGroupOf(filters.categories[0]) : '')
})
const groupQuery = computed(() =>
  currentGroup.value ? `?group=${encodeURIComponent(currentGroup.value)}` : '',
)
const scopeTitle = computed(() => {
  const g = route.query.group
  if (typeof g === 'string' && g) return `${g}维护`
  const c = route.query.category
  if (typeof c === 'string' && c) return c
  return config.ledgerName('maintenance')
})
const scopeDesc = computed(() => {
  const g = route.query.group
  if (typeof g === 'string' && g) return `管理「${g}」分组下的全部运维任务`
  const c = route.query.category
  if (typeof c === 'string' && c) return `管理「${c}」分类下的运维任务`
  return `按 ${config.categoryGroups().map((x) => x.label).join(' / ')} 分组管理全部运维任务`
})

function buildParams() {
  return {
    keyword: filters.keyword,
    status: filters.status,
    categories: filters.categories,
    related_system: filters.related_system,
    handler: filters.handler,
    requester: filters.requester,
    department_id: filters.department_id,
    start_date: filters.start_date || undefined,
    end_date: filters.end_date || undefined,
    page: page.page,
    page_size: page.page_size,
  }
}

async function load() {
  loading.value = true
  try {
    const r = await maintenanceApi.list(buildParams())
    rows.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}
function onSearch() {
  page.page = 1
  load()
}
function onReset() {
  Object.assign(filters, {
    keyword: '', status: '', categories: [], related_system: '', handler: '', requester: '',
    department_id: null, start_date: '', end_date: '',
  })
  onSearch()
}
function onExport() {
  const p = buildParams()
  delete (p as any).page
  delete (p as any).page_size
  const qs = new URLSearchParams(p as any).toString()
  download(`/maintenance-records/export?${qs}`, '通用维护台账.xlsx')
}
async function onDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除维护记录「${row.record_no}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await maintenanceApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

// 行内快速状态流转（pending → processing → resolved/unresolved → closed）
const STATUS_TRANSITIONS: Record<string, string[]> = {
  pending: ['processing', 'resolved', 'unresolved', 'closed'],
  processing: ['resolved', 'unresolved', 'closed'],
  resolved: ['closed'],
  unresolved: ['processing', 'closed'],
  closed: [],
}
async function onQuickStatus(row: any, status: string) {
  try {
    await maintenanceApi.update(row.id, { status })
    ElMessage.success(`状态已更新为「${STATUS_LABELS.maintenance[status] || status}」`)
    load()
  } catch {
    /* handled by interceptor */
  }
}

// 分类标签配色（按业务分组区分；自定义分组默认 info 灰）
const GROUP_TAG_TYPE: Record<string, 'primary' | 'success' | 'warning' | 'danger'> = {
  账号类: 'primary',
  终端类: 'success',
  网络类: 'warning',
  无线类: 'danger',
}
function catTagType(cat: string | null) {
  return cat ? GROUP_TAG_TYPE[config.categoryGroupOf(cat)] || 'info' : 'info'
}

onMounted(async () => {
  config.fetch()
  applyQuery()
  try {
    const d = await departmentApi.list({ page_size: 200 })
    departments.value = d.items
  } catch {
    /* ignore */
  }
  load()
})

// 工作台点击不同分类进入同一路由时，复用组件并刷新筛选
watch(
  () => route.fullPath,
  () => {
    applyQuery()
    onSearch()
  },
)
</script>

<template>
  <div>
    <PageHeader :title="scopeTitle" :description="scopeDesc" icon="Tools">
      <el-button v-permission="'maintenance:create'" type="primary" @click="router.push(`/maintenance/new${groupQuery}`)">
        <el-icon style="margin-right: 4px"><Plus /></el-icon>新增记录
      </el-button>
      <el-button v-permission="'maintenance:export'" @click="onExport">
        <el-icon style="margin-right: 4px"><Download /></el-icon>导出
      </el-button>
    </PageHeader>

    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="问题/结果" clearable style="width: 160px" @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filters.categories" multiple collapse-tags placeholder="全部" clearable style="width: 200px">
            <el-option-group v-for="g in categoryGroups" :key="g.label" :label="g.label">
              <el-option v-for="c in g.options" :key="c" :label="c" :value="c" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="关联系统">
          <el-input v-model="filters.related_system" placeholder="如 NCE-Campus" clearable style="width: 140px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
          <el-button @click="onReset">重置</el-button>
          <el-link type="primary" :underline="false" style="margin-left: 6px" @click="showMore = !showMore">
            {{ showMore ? '收起筛选' : '更多筛选' }}
            <el-icon style="margin-left: 2px; transition: transform 0.2s" :style="{ transform: showMore ? 'rotate(180deg)' : '' }">
              <ArrowDown />
            </el-icon>
          </el-link>
        </el-form-item>
        <template v-if="showMore">
          <el-form-item label="经办人">
            <el-input v-model="filters.handler" placeholder="经办人" clearable style="width: 140px" />
          </el-form-item>
          <el-form-item label="报修人">
            <el-input v-model="filters.requester" placeholder="报修人" clearable style="width: 140px" />
          </el-form-item>
          <el-form-item label="部门">
            <el-select v-model="filters.department_id" placeholder="全部" clearable style="width: 150px">
              <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="时间">
            <el-date-picker v-model="filters.start_date" type="date" value-format="YYYY-MM-DD" placeholder="起始" style="width: 135px" />
            <span style="margin: 0 6px">至</span>
            <el-date-picker v-model="filters.end_date" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width: 135px" />
          </el-form-item>
        </template>
      </el-form>
    </el-card>

    <el-card shadow="never" class="list-card">
      <div class="toolbar">
        <span class="total-text">共 {{ total }} 条记录</span>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="record_no" label="编号" width="140" />
        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            <el-tag :type="catTagType(row.category)" size="small" effect="plain">
              {{ row.category || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="requester" label="报修人" width="100" />
        <el-table-column prop="department_name" label="部门" width="110" />
        <el-table-column prop="location" label="地点" width="120" show-overflow-tooltip />
        <el-table-column prop="related_system" label="关联系统/设备" width="140" show-overflow-tooltip />
        <el-table-column prop="handler" label="经办人" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag module="maintenance" :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="时长" width="100">
          <template #default="{ row }">{{ fmtDuration(row.started_at, row.finished_at) }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="210" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/maintenance/${row.id}${groupQuery}`)">详情</el-button>
            <el-button link type="primary" @click="router.push(`/maintenance/${row.id}/edit${groupQuery}`)">编辑</el-button>
            <el-dropdown
              v-if="STATUS_TRANSITIONS[row.status]?.length"
              trigger="click"
              @command="(s: string) => onQuickStatus(row, s)"
            >
              <el-button link type="primary" v-permission="'maintenance:update'">
                流转<el-icon style="margin-left: 2px"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-for="s in STATUS_TRANSITIONS[row.status]" :key="s" :command="s">
                    → {{ STATUS_LABELS.maintenance[s] || s }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
            <el-button link type="danger" v-permission="'maintenance:delete'" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <EmptyHint text="暂无维护记录">
            <el-button v-if="total === 0" type="primary" @click="router.push(`/maintenance/new${groupQuery}`)">
              新增第一条记录
            </el-button>
          </EmptyHint>
        </template>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="total, sizes, prev, pager, next"
        :total="total"
        :page-size="page.page_size"
        :current-page="page.page"
        :page-sizes="[10, 20, 50, 100]"
        @current-change="(p: number) => { page.page = p; load() }"
        @size-change="(s: number) => { page.page_size = s; page.page = 1; load() }"
      />
    </el-card>
  </div>
</template>

<style scoped>
.filter-card :deep(.el-form-item) {
  margin-bottom: 12px;
}
.list-card {
  margin-top: 14px;
}
.toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 12px;
}
.total-text {
  color: #909399;
  font-size: 13px;
}
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
