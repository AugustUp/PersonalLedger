<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { meetingApi, download } from '@/api'
import { fmtDateTime } from '@/utils/format'
import { STATUS_LABELS } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyHint from '@/components/EmptyHint.vue'

const router = useRouter()
const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)

const filters = reactive({
  keyword: '',
  status: '',
  location: '',
  contact_name: '',
  technicians: '',
  start_date: '',
  end_date: '',
})
const page = reactive({ page: 1, page_size: 20 })

const statusOptions = Object.entries(STATUS_LABELS.meeting).map(([v, l]) => ({ value: v, label: l }))

function buildParams() {
  return {
    keyword: filters.keyword,
    status: filters.status,
    location: filters.location,
    contact_name: filters.contact_name,
    technicians: filters.technicians,
    start_date: filters.start_date || undefined,
    end_date: filters.end_date || undefined,
    page: page.page,
    page_size: page.page_size,
  }
}

async function load() {
  loading.value = true
  try {
    const r = await meetingApi.list(buildParams())
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
  filters.keyword = ''
  filters.status = ''
  filters.location = ''
  filters.contact_name = ''
  filters.technicians = ''
  filters.start_date = ''
  filters.end_date = ''
  onSearch()
}

function onExport() {
  const p = buildParams()
  delete (p as any).page
  delete (p as any).page_size
  const qs = new URLSearchParams(p as any).toString()
  download(`/meetings/export?${qs}`, '会议调试台账.xlsx')
}

async function onDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确认删除会议「${row.meeting_name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await meetingApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="会议调试台账" description="登记会议调试任务、设备与处理过程，跟踪保障状态" icon="Calendar">
      <el-button v-permission="'meeting:create'" type="primary" @click="router.push('/meetings/new')">
        <el-icon style="margin-right: 4px"><Plus /></el-icon>新增会议
      </el-button>
      <el-button v-permission="'meeting:export'" @click="onExport">
        <el-icon style="margin-right: 4px"><Download /></el-icon>导出
      </el-button>
    </PageHeader>
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="名称/内容" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 130px">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="filters.location" placeholder="地点" clearable />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="filters.contact_name" placeholder="联系人" clearable />
        </el-form-item>
        <el-form-item label="调试人员">
          <el-input v-model="filters.technicians" placeholder="调试人员" clearable />
        </el-form-item>
        <el-form-item label="时间">
          <el-date-picker
            v-model="filters.start_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="起始"
            style="width: 140px"
          />
          <span style="margin: 0 6px">至</span>
          <el-date-picker
            v-model="filters.end_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="结束"
            style="width: 140px"
          />
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
        <el-table-column prop="record_no" label="编号" width="140" />
        <el-table-column prop="meeting_name" label="会议名称" min-width="160" show-overflow-tooltip />
        <el-table-column label="时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.meeting_time) }}</template>
        </el-table-column>
        <el-table-column prop="location" label="地点" width="120" show-overflow-tooltip />
        <el-table-column prop="contact_name" label="联系人" width="100" />
        <el-table-column prop="technicians" label="调试人员" width="120" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag module="meeting" :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="更新时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/meetings/${row.id}`)">详情</el-button>
            <el-button link type="primary" @click="router.push(`/meetings/${row.id}/edit`)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <EmptyHint text="暂无会议调试记录">
            <el-button v-if="total === 0" size="small" type="primary" plain @click="router.push('/meetings/new')">
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
