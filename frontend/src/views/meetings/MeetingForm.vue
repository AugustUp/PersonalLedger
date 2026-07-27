<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { meetingApi } from '@/api'
import { STATUS_LABELS } from '@/api/types'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const id = route.params.id ? Number(route.params.id) : null

const form = reactive({
  meeting_name: '',
  meeting_time: '' as string,
  location: '',
  contact_name: '',
  contact_phone: '',
  technicians: '',
  equipment: '',
  debug_content: '',
  problem_description: '',
  handling_process: '',
  result: '',
  onsite_support: false,
  status: 'pending',
  remark: '',
})

const rules: FormRules = {
  meeting_name: [{ required: true, message: '请输入会议名称', trigger: 'blur' }],
}

const statusOptions = Object.entries(STATUS_LABELS.meeting).map(([v, l]) => ({ value: v, label: l }))

function toPayload() {
  const p: Record<string, any> = { ...form }
  if (p.meeting_time === '') p.meeting_time = null
  return p
}

onMounted(async () => {
  if (id) {
    loading.value = true
    try {
      const d = await meetingApi.get(id)
      Object.assign(form, {
        meeting_name: d.meeting_name,
        meeting_time: d.meeting_time || '',
        location: d.location || '',
        contact_name: d.contact_name || '',
        contact_phone: d.contact_phone || '',
        technicians: d.technicians || '',
        equipment: d.equipment || '',
        debug_content: d.debug_content || '',
        problem_description: d.problem_description || '',
        handling_process: d.handling_process || '',
        result: d.result || '',
        onsite_support: d.onsite_support,
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
        await meetingApi.update(id, toPayload())
        ElMessage.success('更新成功')
      } else {
        await meetingApi.create(toPayload())
        ElMessage.success('创建成功')
      }
      router.push('/meetings')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <el-card v-loading="loading" shadow="never">
    <template #header>
      <span>{{ id ? '编辑会议调试' : '新增会议调试' }}</span>
    </template>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" style="max-width: 760px">
      <el-form-item label="会议名称" prop="meeting_name">
        <el-input v-model="form.meeting_name" placeholder="请输入会议名称" />
      </el-form-item>
      <el-form-item label="会议时间">
        <el-date-picker
          v-model="form.meeting_time"
          type="datetime"
          value-format="YYYY-MM-DD HH:mm:ss"
          placeholder="选择时间"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="地点">
        <el-input v-model="form.location" />
      </el-form-item>
      <el-form-item label="联系人">
        <el-input v-model="form.contact_name" />
      </el-form-item>
      <el-form-item label="联系电话">
        <el-input v-model="form.contact_phone" />
      </el-form-item>
      <el-form-item label="调试人员">
        <el-input v-model="form.technicians" placeholder="多个用逗号分隔" />
      </el-form-item>
      <el-form-item label="设备">
        <el-input v-model="form.equipment" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="调试内容">
        <el-input v-model="form.debug_content" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="问题">
        <el-input v-model="form.problem_description" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="处理过程">
        <el-input v-model="form.handling_process" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="结果">
        <el-input v-model="form.result" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="现场保障">
        <el-switch v-model="form.onsite_support" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="form.status" style="width: 200px">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
        <el-button @click="router.push('/meetings')">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>
