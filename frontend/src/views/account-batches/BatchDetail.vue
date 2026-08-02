<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { accountBatchApi, download } from '@/api'
import { fmt, fmtDate, fmtDateTime } from '@/utils/format'
import { STATUS_LABELS } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'
import PageHeader from '@/components/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const id = Number(route.params.id)
const detail = ref<any>(null)
const items = ref<any[]>([])
const total = ref(0)

const filters = reactive({ result: '', keyword: '' })
const page = reactive({ page: 1, page_size: 20 })

const resultOptions = Object.entries(STATUS_LABELS.account_item).map(([v, l]) => ({ value: v, label: l }))

// batch result update
const selected = ref<any[]>([])
const batchDialog = ref(false)
const batchForm = reactive({ result: 'success', failure_reason: '' })
const batchSaving = ref(false)

function buildParams() {
  return { result: filters.result, keyword: filters.keyword, page: page.page, page_size: page.page_size }
}

async function loadDetail() {
  detail.value = await accountBatchApi.get(id)
}
async function loadItems() {
  loading.value = true
  try {
    const r = await accountBatchApi.items(id, buildParams())
    items.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.page = 1
  loadItems()
}
function openImport() {
  router.push(`/account-batches/${id}/import`)
}
function onExport(which: string) {
  download(`/account-batches/${id}/export?which=${which}`, `账号名单_${which}.xlsx`)
}

function onSelectionChange(rows: any[]) {
  selected.value = rows
}
async function openBatchUpdate() {
  if (!selected.value.length) {
    ElMessage.warning('请先勾选要更新的明细')
    return
  }
  batchForm.result = 'success'
  batchForm.failure_reason = ''
  batchDialog.value = true
}
async function submitBatchUpdate() {
  batchSaving.value = true
  try {
    const payload = selected.value.map((r) => ({
      id: r.id,
      result: batchForm.result,
      failure_reason: batchForm.result === 'failed' ? batchForm.failure_reason : null,
    }))
    await accountBatchApi.batchResult(id, payload)
    ElMessage.success('已更新')
    batchDialog.value = false
    await loadItems()
    await loadDetail()
  } finally {
    batchSaving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await loadDetail()
    await loadItems()
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading">
    <PageHeader
      :title="detail?.batch_name || '账号批次详情'"
      :description="detail ? `编号 ${detail.batch_no}` : ''"
      icon="Files"
    >
      <el-button v-permission="'account_batch:update'" type="primary" @click="router.push(`/account-batches/${id}/edit`)">
        编辑批次
      </el-button>
      <el-button v-permission="'account_batch:import'" @click="openImport">导入名单</el-button>
      <el-dropdown v-permission="'account_batch:export'" @command="(c: string) => onExport(c)">
        <el-button>
          导出<el-icon><ArrowDown /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="all">导出全部</el-dropdown-item>
            <el-dropdown-item command="success">成功名单</el-dropdown-item>
            <el-dropdown-item command="failed">失败名单</el-dropdown-item>
            <el-dropdown-item command="pending">待处理名单</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button @click="router.push('/account-batches')">返回列表</el-button>
    </PageHeader>
    <el-card v-if="detail" shadow="never">
      <el-descriptions :column="3" border>
        <el-descriptions-item label="状态"><StatusTag module="account_batch" :status="detail.status" /></el-descriptions-item>
        <el-descriptions-item label="账号类型">{{ fmt(detail.account_type) }}</el-descriptions-item>
        <el-descriptions-item label="申请部门">{{ fmt(detail.applicant_department) }}</el-descriptions-item>
        <el-descriptions-item label="申请人">{{ fmt(detail.applicant) }}</el-descriptions-item>
        <el-descriptions-item label="经办人">{{ fmt(detail.handler) }}</el-descriptions-item>
        <el-descriptions-item label="申请日期">{{ fmtDate(detail.application_date) }}</el-descriptions-item>
        <el-descriptions-item label="总数">{{ detail.total_count }}</el-descriptions-item>
        <el-descriptions-item label="成功/失败/待">{{ detail.success_count }} / {{ detail.failed_count }} / {{ detail.pending_count }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="3">{{ fmt(detail.remark) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">账号明细</el-divider>

      <el-form :inline="true" @submit.prevent>
        <el-form-item label="结果">
          <el-select v-model="filters.result" placeholder="全部" clearable style="width: 130px" @change="onSearch">
            <el-option v-for="o in resultOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="filters.keyword" placeholder="姓名/账号" clearable @keyup.enter="onSearch" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="onSearch">查询</el-button>
          <el-button v-permission="'account_batch:update'" type="success" :disabled="!selected.length" @click="openBatchUpdate">
            批量标记结果（{{ selected.length }}）
          </el-button>
        </el-form-item>
      </el-form>

      <el-table :data="items" border stripe @selection-change="onSelectionChange">
        <el-table-column type="selection" width="45" />
        <el-table-column prop="real_name" label="姓名" width="100" />
        <el-table-column prop="identity_no" label="工号/学号" width="130" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column prop="account_name" label="账号" width="130" />
        <el-table-column prop="account_type" label="类型" width="90" />
        <el-table-column prop="permission_type" label="权限" width="90" />
        <el-table-column label="有效期" width="110">
          <template #default="{ row }">{{ fmtDate(row.valid_until) }}</template>
        </el-table-column>
        <el-table-column label="结果" width="90">
          <template #default="{ row }"><StatusTag module="account_item" :status="row.result" /></template>
        </el-table-column>
        <el-table-column prop="failure_reason" label="失败原因" min-width="140" show-overflow-tooltip />
        <el-table-column label="处理时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.processed_at) }}</template>
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
        @current-change="(p: number) => { page.page = p; loadItems() }"
        @size-change="(s: number) => { page.page_size = s; page.page = 1; loadItems() }"
      />
    </el-card>

    <el-dialog v-model="batchDialog" title="批量标记结果" width="460px">
      <el-form label-width="90px">
        <el-form-item label="结果">
          <el-select v-model="batchForm.result" style="width: 200px">
            <el-option v-for="o in resultOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="batchForm.result === 'failed'" label="失败原因">
          <el-input v-model="batchForm.failure_reason" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialog = false">取消</el-button>
        <el-button type="primary" :loading="batchSaving" @click="submitBatchUpdate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
