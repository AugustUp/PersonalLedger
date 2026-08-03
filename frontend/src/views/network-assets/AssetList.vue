<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { networkAssetApi, departmentApi, download } from '@/api'
import { fmtDate, fmtDateTime } from '@/utils/format'
import { STATUS_LABELS } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyHint from '@/components/EmptyHint.vue'
import type { DepartmentOut } from '@/api/types'

const router = useRouter()
const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)
const departments = ref<DepartmentOut[]>([])

const filters = reactive({
  ip_address: '',
  mac_address: '',
  user_name: '',
  department_id: null as number | null,
  building: '',
  room: '',
  status: '',
  keyword: '',
})
const page = reactive({ page: 1, page_size: 20 })

const statusOptions = Object.entries(STATUS_LABELS.network_asset).map(([v, l]) => ({ value: v, label: l }))

function buildParams() {
  return {
    ip_address: filters.ip_address,
    mac_address: filters.mac_address,
    user_name: filters.user_name,
    department_id: filters.department_id,
    building: filters.building,
    room: filters.room,
    status: filters.status,
    keyword: filters.keyword,
    page: page.page,
    page_size: page.page_size,
  }
}

async function load() {
  loading.value = true
  try {
    const r = await networkAssetApi.list(buildParams())
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
    ip_address: '', mac_address: '', user_name: '', department_id: null,
    building: '', room: '', status: '', keyword: '',
  })
  onSearch()
}
function onExport() {
  const p = buildParams()
  delete (p as any).page
  delete (p as any).page_size
  const qs = new URLSearchParams(p as any).toString()
  download(`/network-assets/export?${qs}`, 'IP_MAC台账.xlsx')
}

onMounted(async () => {
  try {
    const d = await departmentApi.list({ page_size: 200 })
    departments.value = d.items
  } catch {
    /* ignore */
  }
  load()
})
</script>

<template>
  <div>
    <PageHeader title="IP/MAC 台账" description="登记终端 IP、MAC 与使用人信息，支持批量导入" icon="Connection">
      <el-button v-permission="'network_asset:create'" type="primary" @click="router.push('/network-assets/new')">
        <el-icon style="margin-right: 4px"><Plus /></el-icon>新增记录
      </el-button>
      <el-button v-permission="'network_asset:import'" @click="router.push('/network-assets/import')">批量导入</el-button>
      <el-button v-permission="'network_asset:export'" @click="onExport">
        <el-icon style="margin-right: 4px"><Download /></el-icon>导出
      </el-button>
    </PageHeader>
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="IP">
          <el-input v-model="filters.ip_address" placeholder="IP 地址" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="MAC">
          <el-input v-model="filters.mac_address" placeholder="MAC 地址" clearable />
        </el-form-item>
        <el-form-item label="使用人">
          <el-input v-model="filters.user_name" placeholder="使用人" clearable />
        </el-form-item>
        <el-form-item label="部门">
          <el-select v-model="filters.department_id" placeholder="全部" clearable style="width: 150px">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="楼宇">
          <el-input v-model="filters.building" placeholder="楼宇" clearable />
        </el-form-item>
        <el-form-item label="房间">
          <el-input v-model="filters.room" placeholder="房间" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 120px">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="设备/账号" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
          <el-button @click="onReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="margin-top: 14px">
      <div class="toolbar">
        <span class="total-text">共 {{ total }} 条记录</span>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="ip_address" label="IP" width="130" />
        <el-table-column prop="mac_address" label="MAC" width="150" />
        <el-table-column prop="user_name" label="使用人" width="100" />
        <el-table-column prop="department_name" label="部门" width="120" />
        <el-table-column prop="device_name" label="设备" min-width="120" show-overflow-tooltip />
        <el-table-column prop="building" label="楼宇" width="90" />
        <el-table-column prop="room" label="房间" width="90" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag module="network_asset" :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="登记日期" width="120">
          <template #default="{ row }">{{ fmtDate(row.registered_at) }}</template>
        </el-table-column>
        <el-table-column label="更新时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/network-assets/${row.id}`)">详情</el-button>
            <el-button link type="primary" @click="router.push(`/network-assets/${row.id}/edit`)">编辑</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <EmptyHint text="暂无 IP/MAC 记录">
            <el-button v-if="total === 0" type="primary" @click="router.push('/network-assets/new')">
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
