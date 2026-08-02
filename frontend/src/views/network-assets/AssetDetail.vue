<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { networkAssetApi } from '@/api'
import { fmt, fmtDate, fmtDateTime } from '@/utils/format'
import StatusTag from '@/components/StatusTag.vue'
import AttachmentManager from '@/components/AttachmentManager.vue'
import PageHeader from '@/components/PageHeader.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const id = Number(route.params.id)
const detail = ref<any>(null)
const histories = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    detail.value = await networkAssetApi.get(id)
    histories.value = await networkAssetApi.histories(id)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading">
    <PageHeader
      :title="detail ? `${detail.ip_address || ''} / ${detail.mac_address || ''}` : 'IP/MAC 详情'"
      :description="detail && detail.user_name ? `使用人：${detail.user_name}` : ''"
      icon="Connection"
    >
      <el-button v-permission="'network_asset:update'" type="primary" @click="router.push(`/network-assets/${id}/edit`)">
        编辑
      </el-button>
      <el-button @click="router.push('/network-assets')">返回列表</el-button>
    </PageHeader>

    <el-card v-if="detail" shadow="never">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="状态">
          <StatusTag module="network_asset" :status="detail.status" />
        </el-descriptions-item>
        <el-descriptions-item label="使用人">{{ fmt(detail.user_name) }}</el-descriptions-item>
        <el-descriptions-item label="部门">{{ fmt(detail.department_name) }}</el-descriptions-item>
        <el-descriptions-item label="设备名称">{{ fmt(detail.device_name) }}</el-descriptions-item>
        <el-descriptions-item label="设备类型">{{ fmt(detail.device_type) }}</el-descriptions-item>
        <el-descriptions-item label="楼宇/房间">{{ fmt(detail.building) }} / {{ fmt(detail.room) }}</el-descriptions-item>
        <el-descriptions-item label="VLAN">{{ fmt(detail.vlan) }}</el-descriptions-item>
        <el-descriptions-item label="交换机/端口">{{ fmt(detail.switch_name) }} / {{ fmt(detail.switch_port) }}</el-descriptions-item>
        <el-descriptions-item label="账号名称">{{ fmt(detail.account_name) }}</el-descriptions-item>
        <el-descriptions-item label="登记日期">{{ fmtDate(detail.registered_at) }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ fmt(detail.remark) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ fmtDateTime(detail.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ fmtDateTime(detail.updated_at) }}</el-descriptions-item>
      </el-descriptions>

      <el-divider content-position="left">变更历史</el-divider>
      <el-timeline v-if="histories.length">
        <el-timeline-item
          v-for="h in histories"
          :key="h.id"
          :timestamp="fmtDateTime(h.changed_at)"
          placement="top"
        >
          <div>
            <strong>{{ h.field_name }}</strong>：{{ fmt(h.old_value) }} → {{ fmt(h.new_value) }}
          </div>
          <div class="history-reason">原因：{{ fmt(h.change_reason) }}</div>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无变更记录" :image-size="60" />

      <el-divider content-position="left">附件</el-divider>
      <AttachmentManager business-type="network-assets" :business-id="id" />
    </el-card>
  </div>
</template>

<style scoped>
.history-reason {
  color: #909399;
  font-size: 12px;
  margin-top: 2px;
}
</style>
