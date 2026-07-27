<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { operationLogApi } from '@/api'
import { fmt, fmtDateTime } from '@/utils/format'

const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)

const filters = reactive({ module: '', action: '', keyword: '', start_date: '', end_date: '' })
const page = reactive({ page: 1, page_size: 20 })

const moduleOptions = [
  { value: 'meeting', label: '会议调试' },
  { value: 'network-asset', label: 'IP/MAC' },
  { value: 'account-batch', label: '账号批次' },
  { value: 'maintenance', label: '通用维护' },
  { value: 'auth', label: '登录认证' },
  { value: 'user', label: '用户管理' },
  { value: 'department', label: '部门管理' },
]

function buildParams() {
  return {
    module: filters.module,
    action: filters.action,
    keyword: filters.keyword,
    start_date: filters.start_date || undefined,
    end_date: filters.end_date || undefined,
    page: page.page,
    page_size: page.page_size,
  }
}

async function load() {
  loading.value = true
  try {
    const r = await operationLogApi.list(buildParams())
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
  Object.assign(filters, { module: '', action: '', keyword: '', start_date: '', end_date: '' })
  onSearch()
}

onMounted(load)
</script>

<template>
  <div>
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="模块">
          <el-select v-model="filters.module" placeholder="全部" clearable style="width: 140px">
            <el-option v-for="o in moduleOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作">
          <el-input v-model="filters.action" placeholder="如 create/delete" clearable />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="描述" clearable @keyup.enter="onSearch" />
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
      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="user_id" label="用户ID" width="90" />
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="action" label="操作" width="100" />
        <el-table-column prop="business_id" label="业务ID" width="100" />
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column prop="request_ip" label="IP" width="130" />
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
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
.filter-card :deep(.el-form-item) {
  margin-bottom: 12px;
}
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
