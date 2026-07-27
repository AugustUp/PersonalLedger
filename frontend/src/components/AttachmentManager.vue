<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { attachmentApi, download } from '@/api'
import { fmtDateTime, fmtSize } from '@/utils/format'
import type { Attachment } from '@/api/types'

const props = defineProps<{ businessType: string; businessId: number | null }>()

const list = ref<Attachment[]>([])
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

async function load() {
  if (!props.businessId) {
    list.value = []
    return
  }
  list.value = await attachmentApi.list(props.businessType, props.businessId)
}

onMounted(load)
watch(() => props.businessId, load)

function pickFile() {
  fileInput.value?.click()
}

async function onFile(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  if (!f) return
  uploading.value = true
  try {
    await attachmentApi.upload(props.businessType, props.businessId as number, f)
    ElMessage.success('上传成功')
    await load()
  } catch {
    /* interceptor already toasts */
  } finally {
    uploading.value = false
    input.value = ''
  }
}

function doDownload(a: Attachment) {
  download(`/attachments/${a.id}/download`, a.original_name)
}

async function doDelete(a: Attachment) {
  try {
    await ElMessageBox.confirm(`确认删除附件「${a.original_name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await attachmentApi.remove(a.id)
  ElMessage.success('已删除')
  await load()
}
</script>

<template>
  <div class="attachment-manager">
    <div class="att-toolbar">
      <el-button type="primary" :loading="uploading" @click="pickFile">上传附件</el-button>
      <input ref="fileInput" type="file" hidden @change="onFile" />
    </div>
    <el-table v-if="list.length" :data="list" size="small" border>
      <el-table-column prop="original_name" label="文件名" min-width="180" />
      <el-table-column label="大小" width="110">
        <template #default="{ row }">{{ fmtSize(row.size) }}</template>
      </el-table-column>
      <el-table-column label="上传时间" width="170">
        <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="doDownload(row)">下载</el-button>
          <el-button link type="danger" @click="doDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="暂无附件" :image-size="60" />
  </div>
</template>

<style scoped>
.attachment-manager {
  margin-top: 8px;
}
.att-toolbar {
  margin-bottom: 12px;
}
</style>
