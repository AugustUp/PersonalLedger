<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardApi } from '@/api'
import { fmtDateTime } from '@/utils/format'
import type { DashboardSummary } from '@/api/types'

const router = useRouter()
const loading = ref(false)
const data = ref<DashboardSummary | null>(null)

const cards = ref([
  { key: 'meeting', title: '会议调试台账', icon: 'Calendar', color: '#409eff', total: 0, pending: 0, to: '/meetings' },
  { key: 'network', title: 'IP/MAC 台账', icon: 'Connection', color: '#67c23a', total: 0, pending: 0, to: '/network-assets' },
  { key: 'account', title: '批量账号台账', icon: 'Files', color: '#e6a23c', total: 0, pending: 0, to: '/account-batches' },
  { key: 'maintenance', title: '通用维护台账', icon: 'Tools', color: '#f56c6c', total: 0, pending: 0, to: '/maintenance' },
])

async function load() {
  loading.value = true
  try {
    data.value = await dashboardApi.summary()
    cards.value[0].total = data.value.meeting_total
    cards.value[0].pending = data.value.meeting_pending
    cards.value[1].total = data.value.network_asset_total
    cards.value[1].pending = data.value.network_asset_active
    cards.value[2].total = data.value.account_batch_total
    cards.value[2].pending = data.value.account_batch_pending
    cards.value[3].total = data.value.maintenance_total
    cards.value[3].pending = data.value.maintenance_pending
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col v-for="c in cards" :key="c.key" :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" @click="router.push(c.to)">
          <div class="stat-icon" :style="{ background: c.color }">
            <el-icon><component :is="c.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-title">{{ c.title }}</div>
            <div class="stat-total">{{ c.total }}</div>
            <div class="stat-sub">待处理 / 进行中：{{ c.pending }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :md="12">
        <el-card shadow="never" header="最近维护事项">
          <el-table :data="data?.recent_maintenance || []" size="small" empty-text="暂无数据">
            <el-table-column prop="record_no" label="编号" width="140" />
            <el-table-column prop="category" label="类别" width="100" />
            <el-table-column prop="status" label="状态" width="90" />
            <el-table-column label="更新时间">
              <template #default="{ row }">{{ fmtDateTime(row.updated_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :md="12">
        <el-card shadow="never" header="最近会议调试">
          <el-table :data="data?.recent_meetings || []" size="small" empty-text="暂无数据">
            <el-table-column prop="record_no" label="编号" width="140" />
            <el-table-column prop="meeting_name" label="名称" min-width="140" />
            <el-table-column prop="status" label="状态" width="90" />
            <el-table-column label="更新时间">
              <template #default="{ row }">{{ fmtDateTime(row.updated_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-card {
  cursor: pointer;
  margin-bottom: 4px;
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 10px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.stat-title {
  color: #606266;
  font-size: 13px;
}
.stat-total {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-sub {
  color: #909399;
  font-size: 12px;
}
</style>
