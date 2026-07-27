<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { meetingApi } from '@/api'
import { fmt, fmtBool, fmtDateTime } from '@/utils/format'
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
    detail.value = await meetingApi.get(id)
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
          <span>{{ detail.meeting_name }}</span>
          <div>
            <el-button v-permission="'meeting:update'" type="primary" @click="router.push(`/meetings/${id}/edit`)">
              编辑
            </el-button>
            <el-button @click="router.push('/meetings')">返回</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="编号">{{ fmt(detail.record_no) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusTag module="meeting" :status="detail.status" />
        </el-descriptions-item>
        <el-descriptions-item label="会议时间">{{ fmtDateTime(detail.meeting_time) }}</el-descriptions-item>
        <el-descriptions-item label="地点">{{ fmt(detail.location) }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ fmt(detail.contact_name) }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ fmt(detail.contact_phone) }}</el-descriptions-item>
        <el-descriptions-item label="调试人员">{{ fmt(detail.technicians) }}</el-descriptions-item>
        <el-descriptions-item label="现场保障">{{ fmtBool(detail.onsite_support) }}</el-descriptions-item>
        <el-descriptions-item label="设备" :span="2">{{ fmt(detail.equipment) }}</el-descriptions-item>
        <el-descriptions-item label="调试内容" :span="2">{{ fmt(detail.debug_content) }}</el-descriptions-item>
        <el-descriptions-item label="问题" :span="2">{{ fmt(detail.problem_description) }}</el-descriptions-item>
        <el-descriptions-item label="处理过程" :span="2">{{ fmt(detail.handling_process) }}</el-descriptions-item>
        <el-descriptions-item label="结果" :span="2">{{ fmt(detail.result) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ fmt(detail.remark) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ fmtDateTime(detail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ fmtDateTime(detail.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">附件</el-divider>
      <AttachmentManager business-type="meetings" :business-id="id" />
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
