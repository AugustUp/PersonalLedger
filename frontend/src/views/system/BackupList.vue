<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { backupApi, type BackupFile } from '@/api'
import { fmtSize } from '@/utils/format'
import PageHeader from '@/components/PageHeader.vue'

const loading = ref(false)
const saving = ref(false)
const rows = ref<BackupFile[]>([])

async function load() {
  loading.value = true
  try {
    rows.value = await backupApi.list()
  } finally {
    loading.value = false
  }
}

async function onCreate() {
  try {
    await ElMessageBox.confirm(
      '将使用 SQLite 快照机制对当前数据库执行在线备份，不会影响正在进行的操作。确认备份？',
      '创建备份',
      { type: 'warning', confirmButtonText: '立即备份' },
    )
  } catch {
    return
  }
  saving.value = true
  try {
    await backupApi.create()
    ElMessage.success('备份成功')
    load()
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader title="数据备份" description="对 SQLite 数据库进行在线快照备份，防止数据丢失" icon="FolderOpened">
      <el-button type="primary" :loading="saving" @click="onCreate">
        <el-icon style="margin-right: 4px"><FolderAdd /></el-icon>立即备份
      </el-button>
    </PageHeader>

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="备份说明"
      description="备份文件保存在数据库同目录的 backups/ 文件夹，自动保留最近 10 份。恢复方式：停止服务后，用备份文件替换 data/ops_ledger.db 再启动即可。"
      style="margin-bottom: 14px"
    />

    <el-card shadow="never">
      <div class="toolbar">
        <span class="total-text">共 {{ rows.length }} 份备份</span>
      </div>
      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="filename" label="备份文件" min-width="260" />
        <el-table-column label="大小" width="140">
          <template #default="{ row }">{{ fmtSize(row.size) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <template #empty>
          <div class="empty-tip">暂无备份，点击右上角「立即备份」创建第一份</div>
        </template>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 12px;
}
.total-text {
  color: #909399;
  font-size: 13px;
}
.empty-tip {
  color: #a8abb2;
  font-size: 13px;
  padding: 24px 0;
}
</style>
