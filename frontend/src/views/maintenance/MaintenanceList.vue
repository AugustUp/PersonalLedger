<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { maintenanceApi, departmentApi, download } from '@/api'
import { fmtDate, fmtDateTime, fmtDuration } from '@/utils/format'
import { STATUS_LABELS, CATEGORY_LABELS, MAINTENANCE_CATEGORY_GROUPS, categoryGroupOf } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'
import type { DepartmentOut } from '@/api/types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const departments = ref<DepartmentOut[]>([])

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
const categoryGroups = MAINTENANCE_CATEGORY_GROUPS

// 支持从工作台（?category=）或侧边栏分组导航（?group=）进入时预筛选
function applyQuery() {
  const q = route.query
  const group = typeof q.group === 'string' ? q.group : ''
  const cat = typeof q.category === 'string' ? q.category : ''
  if (group) {
    const g = MAINTENANCE_CATEGORY_GROUPS.find((x) => x.label === group)
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
  return typeof g === 'string' && g ? g : (filters.categories.length === 1 ? categoryGroupOf(filters.categories[0]) : '')
})
const groupQuery = computed(() =>
  currentGroup.value ? `?group=${encodeURIComponent(currentGroup.value)}` : '',
)
const scopeTitle = computed(() => {
  const g = route.query.group
  if (typeof g === 'string' && g) return `${g}维护`
  const c = route.query.category
  if (typeof c === 'string' && c) return c
  return '通用维护台账'
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

onMounted(async () => {
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
    <h3 class="page-title">{{ scopeTitle }}</h3>
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="问题/结果" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 130px">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="filters.categories" multiple collapse-tags placeholder="全部" clearable style="width: 220px">
            <el-option-group v-for="g in categoryGroups" :key="g.label" :label="g.label">
              <el-option v-for="c in g.options" :key="c" :label="c" :value="c" />
            </el-option-group>
          </el-select>
        </el-form-item>
        <el-form-item label="关联系统">
          <el-input v-model="filters.related_system" placeholder="如 NCE-Campus/深澜/AC" clearable />
        </el-form-item>
        <el-form-item label="经办人">
          <el-input v-model="filters.handler" placeholder="经办人" clearable />
        </el-form-item>
        <el-form-item label="报修人">
          <el-input v-model="filters.requester" placeholder="报修人" clearable />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="filters.department_id" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker v-model="filters.start_date" type="date" value-format="YYYY-MM-DD" placeholder="起始" style="width: 140px" />
          <span style="margin: 0 6px">至</span>
          <el-date-picker v-model="filters.end_date" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width: 140px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="margin-top: 14px">
      <div class="toolbar">
        <div>
          <el-button type="primary" v-permission="'maintenance:create'" @click="router.push(`/maintenance/new${groupQuery}`)">
            新增记录
          </el-button>
          <el-button v-permission="'maintenance:export'" @click="onExport">导出</el-button>
        </div>
        <span class="total-text">共 {{ total }} 条</span>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="record_no" label="编号" width="140" />
        <el-table-column label="分类" width="110">
          <template #default="{ row }">{{ CATEGORY_LABELS[row.category] || row.category || '-' }}</template>
        </el-table-column>
        <el-table-column prop="requester" label="报修人" width="100" />
        <el-table-column prop="department_name" label="部门" width="110" />
        <el-table-column prop="location" label="地点" width="120" show-overflow-tooltip />
        <el-table-column prop="related_system" label="关联系统/设备" width="140" show-overflow-tooltip />
        <el-table-column prop="handler" label="经办人" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag module="maintenance" :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="时长" width="110">
          <template #default="{ row }">{{ fmtDuration(row.started_at, row.finished_at) }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/maintenance/${row.id}${groupQuery}`)">详情</el-button>
            <el-button link type="primary" @click="router.push(`/maintenance/${row.id}/edit${groupQuery}`)">编辑</el-button>
            <el-button link type="danger" v-permission="'maintenance:delete'" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
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
.page-title {
  margin: 0 0 14px;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.filter-card :deep(.el-form-item) {
  margin-bottom: 12px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
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
