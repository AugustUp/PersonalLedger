<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardApi } from '@/api'
import { fmtDateTime } from '@/utils/format'
import { useConfigStore } from '@/stores/config'
import type { DashboardSummary } from '@/api/types'

const router = useRouter()
const config = useConfigStore()
const loading = ref(false)
const data = ref<DashboardSummary | null>(null)

const moduleCards = ref([
  { key: 'meetings', titleKey: 'meetings', icon: 'Calendar', color: '#409eff', total: 0, pending: 0, to: '/meetings' },
  { key: 'network', titleKey: 'network_assets', icon: 'Connection', color: '#67c23a', total: 0, pending: 0, to: '/network-assets' },
  { key: 'account', titleKey: 'account_batches', icon: 'Files', color: '#e6a23c', total: 0, pending: 0, to: '/account-batches' },
  { key: 'maintenance', titleKey: 'maintenance', icon: 'Tools', color: '#f56c6c', total: 0, pending: 0, to: '/maintenance' },
])

const catGroups = computed(() => config.categoryGroups())

function catStat(c: string) {
  const m = data.value?.maintenance_by_category || {}
  return m[c] || { total: 0, pending: 0 }
}

async function load() {
  loading.value = true
  try {
    data.value = await dashboardApi.summary()
    const d = data.value
    moduleCards.value[0].total = d.meeting_total
    moduleCards.value[0].pending = d.meeting_pending
    moduleCards.value[1].total = d.network_asset_total
    moduleCards.value[1].pending = d.network_asset_active
    moduleCards.value[2].total = d.account_batch_total
    moduleCards.value[2].pending = d.account_batch_pending
    moduleCards.value[3].total = d.maintenance_total
    moduleCards.value[3].pending = d.maintenance_pending
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  config.fetch()
  load()
})
</script>

<template>
  <div v-loading="loading">
    <el-card shadow="never" class="quick-card">
      <div class="quick-bar">
        <span class="quick-label">快捷操作</span>
        <el-button v-permission="'meeting:create'" @click="router.push('/meetings/new')">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>新增会议调试
        </el-button>
        <el-button v-permission="'maintenance:create'" type="primary" @click="router.push('/maintenance/new')">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>新增维护记录
        </el-button>
        <el-button v-permission="'network_asset:import'" @click="router.push('/network-assets/import')">
          <el-icon style="margin-right: 4px"><Upload /></el-icon>导入 IP/MAC
        </el-button>
        <el-button v-permission="'account_batch:create'" @click="router.push('/account-batches/new')">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>新增账号批次
        </el-button>
      </div>
    </el-card>

    <h3 class="section-title">业务台账总览</h3>
    <el-row :gutter="16">
      <el-col v-for="c in moduleCards" :key="c.key" :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="stat-card" @click="router.push(c.to)">
          <div class="stat-icon" :style="{ background: c.color }">
            <el-icon><component :is="c.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-title">{{ config.ledgerName(c.titleKey) }}</div>
            <div class="stat-total">{{ c.total }}</div>
            <div class="stat-sub">待处理 / 进行中：{{ c.pending }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="domain-card">
      <template #header>
        <span class="card-header">维护任务领域（点击进入对应分类）</span>
      </template>
      <div v-for="g in catGroups" :key="g.label" class="cat-group">
        <div class="cat-group-title">{{ g.label }}</div>
        <div class="cat-grid">
          <div
            v-for="c in g.options"
            :key="c"
            class="cat-tile"
            @click="router.push(`/maintenance?category=${encodeURIComponent(c)}`)"
          >
            <div class="cat-name">{{ c }}</div>
            <div class="cat-stat">
              <span class="cat-pending">{{ catStat(c).pending }}</span>
              <span class="cat-total"> / {{ catStat(c).total }}</span>
            </div>
            <div class="cat-foot">待办 / 总数</div>
          </div>
        </div>
      </div>
    </el-card>

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
.quick-card {
  margin-bottom: 16px;
}
.quick-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.quick-label {
  font-size: 13px;
  color: #909399;
  margin-right: 4px;
}
.section-title {
  margin: 0 0 12px;
  font-size: 15px;
  color: #303133;
}
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
.domain-card {
  margin-top: 16px;
}
.card-header {
  font-weight: 600;
  color: #303133;
}
.cat-group {
  margin-bottom: 14px;
}
.cat-group-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}
.cat-tile {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  background: #fafafa;
  transition: all 0.15s;
}
.cat-tile:hover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateY(-2px);
}
.cat-name {
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}
.cat-stat {
  font-size: 18px;
  font-weight: 700;
}
.cat-pending {
  color: #f56c6c;
}
.cat-total {
  color: #606266;
}
.cat-foot {
  font-size: 12px;
  color: #909399;
}
</style>
