<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { networkAssetApi } from '@/api'
import type { ImportPreview } from '@/api/types'

const router = useRouter()
const file = ref<File | null>(null)
const preview = ref<ImportPreview | null>(null)
const previewing = ref(false)
const committing = ref(false)
const importing = ref(false)
const sampleColumns = ref<string[]>([])
const strategy = ref<'skip' | 'update'>('skip')

const acceptText =
  'Excel 表头（首行）：ip_address, mac_address, user_name, department_id, device_name, device_type, building, room, vlan, switch_name, switch_port, account_name, status, registered_at, remark'

function onFile(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (!f) return
  file.value = f
  preview.value = null
}

async function onPreview() {
  if (!file.value) {
    ElMessage.warning('请先选择 Excel 文件')
    return
  }
  previewing.value = true
  try {
    const r = await networkAssetApi.importPreview(file.value)
    preview.value = r
    sampleColumns.value = r.sample.length ? Object.keys(r.sample[0]) : []
    if (r.invalid_rows > 0) {
      ElMessage.warning(`有 ${r.invalid_rows} 行存在错误，请查看错误列表`)
    } else {
      ElMessage.success('校验通过，可以导入')
    }
  } finally {
    previewing.value = false
  }
}

async function onCommit() {
  if (!preview.value) return
  importing.value = true
  try {
    await networkAssetApi.importCommit(preview.value.import_token, strategy.value)
    ElMessage.success('导入完成')
    router.push('/network-assets')
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <el-card shadow="never">
    <template #header><span>IP/MAC 批量导入</span></template>

    <el-alert :title="acceptText" type="info" :closable="false" show-icon style="margin-bottom: 16px" />

    <el-upload
      :auto-upload="false"
      :show-file-list="true"
      :limit="1"
      accept=".xlsx,.xls"
      @change="(u: any) => { file = u.raw; preview = null }"
    >
      <el-button type="primary">选择 Excel 文件</el-button>
      <template #tip><div class="el-upload__tip">仅支持 .xlsx / .xls，单文件</div></template>
    </el-upload>

    <div class="actions">
      <el-button :loading="previewing" @click="onPreview">解析预览</el-button>
    </div>

    <template v-if="preview">
      <el-divider>预览结果</el-divider>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="总行数">{{ preview.total_rows }}</el-descriptions-item>
        <el-descriptions-item label="有效行">{{ preview.valid_rows }}</el-descriptions-item>
        <el-descriptions-item label="错误行">{{ preview.invalid_rows }}</el-descriptions-item>
      </el-descriptions>

      <div v-if="preview.errors.length" class="error-box">
        <div class="error-title">错误列表（共 {{ preview.errors.length }} 条）</div>
        <el-table :data="preview.errors.slice(0, 100)" size="small" border max-height="240">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="field" label="字段" width="140" />
          <el-table-column prop="message" label="说明" />
        </el-table>
      </div>

      <div v-if="preview.sample.length" style="margin-top: 12px">
        <div class="error-title">数据样例</div>
        <el-table :data="preview.sample.slice(0, 10)" size="small" border max-height="240">
          <el-table-column v-for="c in sampleColumns" :key="c" :prop="c" :label="c" />
        </el-table>
      </div>

      <el-divider />
      <el-form label-width="120px" inline>
        <el-form-item label="导入策略">
          <el-radio-group v-model="strategy">
            <el-radio value="skip">仅新增（冲突跳过）</el-radio>
            <el-radio value="update">允许更新已有</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <el-button type="success" :loading="importing" @click="onCommit">确认导入</el-button>
    </template>
  </el-card>
</template>

<style scoped>
.actions {
  margin-top: 12px;
}
.error-box {
  margin-top: 12px;
}
.error-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #606266;
}
</style>
