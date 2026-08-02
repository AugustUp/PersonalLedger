<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountBatchApi, download } from '@/api'
import { fmtDate, fmtDateTime } from '@/utils/format'
import { STATUS_LABELS } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'
import PageHeader from '@/components/PageHeader.vue'
import EmptyHint from '@/components/EmptyHint.vue'

const router = useRouter()
const loading = ref(false)
const rows = ref<any[]>([])
const total = ref(0)

const filters = reactive({
  batch_name: '',
  account_type: '',
  status: '',
  applicant: '',
  start_date: '',
  end_date: '',
})
const page = reactive({ page: 1, page_size: 20 })

const statusOptions = Object.entries(STATUS_LABELS.account_batch).map(([v, l]) => ({ value: v, label: l }))

function buildParams() {
  return {
    batch_name: filters.batch_name,
    account_type: filters.account_type,
    status: filters.status,
    applicant: filters.applicant,
    start_date: filters.start_date || undefined,
    end_date: filters.end_date || undefined,
    page: page.page,
    page_size: page.page_size,
  }
}

async function load() {
  loading.value = true
  try {
    const r = await accountBatchApi.list(buildParams())
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
  Object.assign(filters, { batch_name: '', account_type: '', status: '', applicant: '', start_date: '', end_date: '' })
  onSearch()
}
function onTemplate() {
  download('/account-batches/export-template', '账号导入模板.xlsx')
}
async function onDelete(row: any) {
  try {
    await ElMessageBox.confirm(`确认作废批次「${row.batch_name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await accountBatchApi.remove(row.id)
  ElMessage.success('已作废')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="批量账号台账" description="按批次管理 OA / 邮箱等账号的开通与导入记录" icon="Files">
      <el-button v-permission="'account_batch:create'" type="primary" @click="router.push('/account-batches/new')">
        <el-icon style="margin-right: 4px"><Plus /></el-icon>新增批次
      </el-button>
      <el-button v-permission="'account_batch:import'" @click="onTemplate">
        <el-icon style="margin-right: 4px"><Download /></el-icon>下载模板
      </el-button>
    </PageHeader>
    <el-card shadow="never" class="filter-card">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="批次名称">
          <el-input v-model="filters.batch_name" placeholder="名称" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item label="账号类型">
          <el-input v-model="filters.account_type" placeholder="类型" clearable />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width: 130px">
            <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="申请人">
          <el-input v-model="filters.applicant" placeholder="申请人" clearable />
        </el-form-item>
        <el-form-item label="申请日期">
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
        <span class="total-text">共 {{ total }} 条记录</span>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="batch_no" label="编号" width="140" />
        <el-table-column prop="batch_name" label="批次名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="account_type" label="类型" width="100" />
        <el-table-column prop="applicant" label="申请人" width="100" />
        <el-table-column prop="applicant_department" label="申请部门" width="120" />
        <el-table-column label="统计" width="180">
          <template #default="{ row }">
            总 {{ row.total_count }} / 成功 {{ row.success_count }} / 失败 {{ row.failed_count }} / 待 {{ row.pending_count }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><StatusTag module="account_batch" :status="row.status" /></template>
        </el-table-column>
        <el-table-column label="申请日期" width="120">
          <template #default="{ row }">{{ fmtDate(row.application_date) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="190" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="router.push(`/account-batches/${row.id}`)">详情</el-button>
            <el-button link type="primary" @click="router.push(`/account-batches/${row.id}/edit`)">编辑</el-button>
            <el-button link type="danger" v-permission="'account_batch:delete'" @click="onDelete(row)">作废</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <EmptyHint text="暂无账号批次">
            <el-button v-if="total === 0" size="small" type="primary" plain @click="router.push('/account-batches/new')">
              新增第一个批次
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
