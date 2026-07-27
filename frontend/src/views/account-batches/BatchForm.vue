<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { accountBatchApi } from '@/api'
import { STATUS_LABELS } from '@/api/types'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const id = route.params.id ? Number(route.params.id) : null

const form = reactive({
  batch_name: '',
  account_type: '',
  applicant_department: '',
  applicant: '',
  application_date: '' as string,
  handler: '',
  status: 'draft',
  remark: '',
})

const rules: FormRules = {
  batch_name: [{ required: true, message: '请输入批次名称', trigger: 'blur' }],
}

const statusOptions = Object.entries(STATUS_LABELS.account_batch).map(([v, l]) => ({ value: v, label: l }))

function toPayload() {
  const p: Record<string, any> = { ...form }
  if (p.application_date === '') p.application_date = null
  if (!id) delete p.status
  return p
}

onMounted(async () => {
  if (id) {
    loading.value = true
    try {
      const d = await accountBatchApi.get(id)
      Object.assign(form, {
        batch_name: d.batch_name,
        account_type: d.account_type || '',
        applicant_department: d.applicant_department || '',
        applicant: d.applicant || '',
        application_date: d.application_date || '',
        handler: d.handler || '',
        status: d.status,
        remark: d.remark || '',
      })
    } finally {
      loading.value = false
    }
  }
})

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      if (id) {
        await accountBatchApi.update(id, toPayload())
        ElMessage.success('更新成功')
      } else {
        const created = await accountBatchApi.create(toPayload())
        ElMessage.success('创建成功，可继续导入名单')
        router.replace(`/account-batches/${created.id}`)
        return
      }
      router.push('/account-batches')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <el-card v-loading="loading" shadow="never">
    <template #header><span>{{ id ? '编辑账号批次' : '新增账号批次' }}</span></template>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px" style="max-width: 640px">
      <el-form-item label="批次名称" prop="batch_name">
        <el-input v-model="form.batch_name" />
      </el-form-item>
      <el-form-item label="账号类型">
        <el-input v-model="form.account_type" placeholder="如 邮箱 / 钉钉 / VPN" />
      </el-form-item>
      <el-form-item label="申请部门">
        <el-input v-model="form.applicant_department" />
      </el-form-item>
      <el-form-item label="申请人">
        <el-input v-model="form.applicant" />
      </el-form-item>
      <el-form-item label="申请日期">
        <el-date-picker v-model="form.application_date" type="date" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item label="经办人">
        <el-input v-model="form.handler" />
      </el-form-item>
      <el-form-item v-if="id" label="状态">
        <el-select v-model="form.status" style="width: 200px">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
        <el-button @click="router.push(id ? `/account-batches/${id}` : '/account-batches')">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>
