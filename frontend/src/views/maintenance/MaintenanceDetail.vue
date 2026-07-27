<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { maintenanceApi } from '@/api'
import { fmt, fmtDateTime, fmtDuration } from '@/utils/format'
import { CATEGORY_LABELS } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'
import AttachmentManager from '@/components/AttachmentManager.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const id = Number(route.params.id)
const detail = ref<any>(null)

onMounted(async () => {
  loading.value = true
  try {
    detail.value = await maintenanceApi.get(id)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading">
    <el-card v-if="detail" shadow="never">
      <template #header>
        <div class="detail-head">
          <span>{{ detail.record_no }}</span>
          <div>
            <el-button v-permission="'maintenance:update'" type="primary" @click="router.push(`/maintenance/${id}/edit`)">
              编辑
            </el-button>
            <el-button @click="router.push('/maintenance')">返回</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="状态">
          <StatusTag module="maintenance" :status="detail.status" />
        </el-descriptions-item>
        <el-descriptions-item label="报修人">{{ fmt(detail.requester) }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ fmt(detail.department_name) }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ fmt(detail.contact_phone) }}</el-descriptions-item>
        <el-descriptions-item label="地点">{{ fmt(detail.location) }}</el-descriptions-item>
        <el-descriptions-item label="分类">{{ CATEGORY_LABELS[detail.category] || detail.category || '-' }}</el-descriptions-item>
        <el-descriptions-item label="关联系统/设备">{{ fmt(detail.related_system) }}</el-descriptions-item>
        <el-descriptions-item label="经办人">{{ fmt(detail.handler) }}</el-descriptions-item>
        <el-descriptions-item label="处理时长">{{ fmtDuration(detail.started_at, detail.finished_at) }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ fmtDateTime(detail.started_at) }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ fmtDateTime(detail.finished_at) }}</el-descriptions-item>
        <el-descriptions-item label="问题描述" :span="2">{{ fmt(detail.problem_description) }}</el-descriptions-item>
        <el-descriptions-item label="处理过程" :span="2">{{ fmt(detail.handling_process) }}</el-descriptions-item>
        <el-descriptions-item label="故障原因" :span="2">{{ fmt(detail.fault_cause) }}</el-descriptions-item>
        <el-descriptions-item label="处理结果" :span="2">{{ fmt(detail.result) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ fmt(detail.remark) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ fmtDateTime(detail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ fmtDateTime(detail.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">附件</el-divider>
      <AttachmentManager business-type="maintenance" :business-id="id" />
    </el-card>
  </div>
</template>

<style scoped>
.detail-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}
</style>
