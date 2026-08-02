<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { dashboardApi, maintenanceApi, meetingApi } from '@/api'
import { useConfigStore } from '@/stores/config'
import { STATUS_LABELS } from '@/api/types'
import StatusTag from '@/components/StatusTag.vue'
import QuickAddDialog from '@/components/QuickAddDialog.vue'
import type { DashboardSummary } from '@/api/types'

const router = useRouter()
const config = useConfigStore()
const loading = ref(false)
const data = ref<DashboardSummary | null>(null)
const quickVisible = ref(false)

const moduleCards = ref([
  { key: 'meetings', titleKey: 'meetings', icon: 'Calendar', color: 'linear-gradient(135deg,#6366f1,#8b5cf6)', total: 0, pending: 0, to: '/meetings' },
  { key: 'network', titleKey: 'network_assets', icon: 'Connection', color: 'linear-gradient(135deg,#10b981,#34d399)', total: 0, pending: 0, to: '/network-assets' },
  { key: 'account', titleKey: 'account_batches', icon: 'Files', color: 'linear-gradient(135deg,#f59e0b,#fbbf24)', total: 0, pending: 0, to: '/account-batches' },
  { key: 'maintenance', titleKey: 'maintenance', icon: 'Tools', color: 'linear-gradient(135deg,#ef4444,#f87171)', total: 0, pending: 0, to: '/maintenance' },
])

const catGroups = computed(() => config.categoryGroups())

function catStat(c: string) {
  const m = data.value?.maintenance_by_category || {}
  return m[c] || { total: 0, pending: 0 }
}

const todayCards = computed(() => {
  const d = data.value
  return [
    { label: '今日维护', value: d?.today_maintenance ?? 0, to: '/maintenance' },
    { label: '今日会议', value: d?.today_meetings ?? 0, to: '/meetings' },
    { label: '今日 IP/MAC', value: d?.today_assets ?? 0, to: '/network-assets' },
    { label: '今日批次', value: d?.today_batches ?? 0, to: '/account-batches' },
  ]
})

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

// 待办行内状态流转（维护）
const MAINT_TRANSITIONS: Record<string, string[]> = {
  pending: ['processing', 'resolved'],
  processing: ['resolved'],
}
async function onTodoStatus(row: any, status: string) {
  try {
    await maintenanceApi.update(row.id, { status })
    ElMessage.success(`已更新为「${STATUS_LABELS.maintenance[status] || status}」`)
    load()
  } catch {
    /* interceptor */
  }
}
async function onMeetingStatus(row: any, status: string) {
  try {
    await meetingApi.update(row.id, { status })
    ElMessage.success(`已更新为「${STATUS_LABELS.meeting[status] || status}」`)
    load()
  } catch {
    /* interceptor */
  }
}

onMounted(() => {
  config.fetch()
  load()
})
</script>

<template>
  <div v-loading="loading">
    <!-- 快速登记 -->
    <el-card shadow="never" class="quick-card">
      <div class="quick-bar">
        <el-button type="primary" size="large" class="quick-add-btn" @click="quickVisible = true">
          <el-icon style="margin-right: 6px"><Plus /></el-icon>快速登记
        </el-button>
        <span class="quick-hint">记一条留底：选类型 → 填关键信息 → 保存，可连续录入</span>
        <el-button v-permission="'network_asset:import'" text @click="router.push('/network-assets/import')">导入 IP/MAC</el-button>
        <el-button v-permission="'account_batch:create'" text @click="router.push('/account-batches/new')">新增账号批次</el-button>
      </div>
    </el-card>

    <!-- 今日新增 -->
    <el-row :gutter="12" style="margin-top: 12px">
      <el-col v-for="t in todayCards" :key="t.label" :xs="12" :sm="6">
        <div class="today-chip" @click="router.push(t.to)">
          <span class="today-num">{{ t.value }}</span>
          <span class="today-label">{{ t.label }}</span>
        </div>
      </el-col>
    </el-row>

    <!-- 待办清单 -->
    <el-row :gutter="16" style="margin-top: 16px">
      <el-col :md="14">
        <el-card shadow="never" header="待办 · 维护事项（待处理/处理中）" class="todo-card">
          <el-table :data="data?.todo_maintenance || []" size="small">
            <el-table-column prop="record_no" label="编号" width="140" />
            <el-table-column prop="category" label="分类" width="110" />
            <el-table-column prop="requester" label="报修人" width="90" />
            <el-table-column prop="location" label="地点" min-width="90" show-overflow-tooltip />
            <el-table-column label="状态" width="95">
              <template #default="{ row }"><StatusTag module="maintenance" :status="row.status" /></template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-dropdown v-if="MAINT_TRANSITIONS[row.status]?.length" trigger="click" @command="(s: string) => onTodoStatus(row, s)">
                  <el-button link type="primary">流转<el-icon style="margin-left: 2px"><ArrowDown /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-for="s in MAINT_TRANSITIONS[row.status]" :key="s" :command="s">
                        → {{ STATUS_LABELS.maintenance[s] || s }}
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button link type="primary" @click="router.push(`/maintenance/${row.id}`)">详情</el-button>
              </template>
            </el-table-column>
            <template #empty><span class="todo-empty">暂无待办，今天都处理完啦 🎉</span></template>
          </el-table>
        </el-card>
      </el-col>
      <el-col :md="10">
        <el-card shadow="never" header="待办 · 会议调试（待调试）" class="todo-card">
          <el-table :data="data?.todo_meetings || []" size="small">
            <el-table-column prop="record_no" label="编号" width="140" />
            <el-table-column prop="meeting_name" label="名称" min-width="110" show-overflow-tooltip />
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-dropdown v-if="row.status === 'pending'" trigger="click" @command="(s: string) => onMeetingStatus(row, s)">
                  <el-button link type="primary">流转<el-icon style="margin-left: 2px"><ArrowDown /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="debugged">→ 已调试</el-dropdown-item>
                      <el-dropdown-item command="completed">→ 已完成</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <el-button link type="primary" @click="router.push(`/meetings/${row.id}`)">详情</el-button>
              </template>
            </el-table-column>
            <template #empty><span class="todo-empty">暂无待调试会议</span></template>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

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

    <QuickAddDialog v-model:visible="quickVisible" @saved="load" />
  </div>
</template>

<style scoped>
.quick-card {
  margin-bottom: 12px;
  border: none;
  background: linear-gradient(120deg, #ffffff 0%, #f3f4ff 100%);
}
.quick-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.quick-add-btn {
  font-size: 15px;
  font-weight: 600;
}
.quick-hint {
  color: #9ca3af;
  font-size: 13px;
}
.today-chip {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid #eef1f7;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}
.today-chip:hover {
  border-color: var(--el-color-primary-light-5);
}
.today-num {
  font-size: 22px;
  font-weight: 700;
  color: var(--el-color-primary);
}
.today-label {
  font-size: 12px;
  color: #9ca3af;
}
.todo-card {
  margin-bottom: 4px;
}
.todo-card :deep(.el-card__header) {
  font-weight: 600;
  color: #1f2937;
}
.todo-empty {
  color: #9ca3af;
  font-size: 13px;
}
.section-title {
  margin: 18px 0 12px;
  font-size: 15px;
  color: #1f2937;
  font-weight: 600;
}
.stat-card {
  cursor: pointer;
  margin-bottom: 4px;
  transition: all 0.2s ease;
}
.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 26px rgba(79, 70, 229, 0.14);
}
.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
}
.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: 0 4px 10px rgba(16, 24, 40, 0.16);
}
.stat-title {
  color: #6b7280;
  font-size: 13px;
}
.stat-total {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
  color: #111827;
}
.stat-sub {
  color: #9ca3af;
  font-size: 12px;
}
.domain-card {
  margin-top: 16px;
}
.card-header {
  font-weight: 600;
  color: #1f2937;
}
.cat-group {
  margin-bottom: 14px;
}
.cat-group-title {
  font-size: 13px;
  color: #8b5cf6;
  margin-bottom: 8px;
  font-weight: 600;
}
.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}
.cat-tile {
  border: 1px solid #eef1f7;
  border-radius: 12px;
  padding: 14px;
  cursor: pointer;
  background: #fff;
  transition: all 0.18s ease;
}
.cat-tile:hover {
  border-color: #c7c3f9;
  background: linear-gradient(135deg, #f4f3ff 0%, #ffffff 100%);
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.12);
}
.cat-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}
.cat-stat {
  font-size: 18px;
  font-weight: 700;
}
.cat-pending {
  color: #ef4444;
}
.cat-total {
  color: #6b7280;
}
.cat-foot {
  font-size: 12px;
  color: #9ca3af;
}
</style>
