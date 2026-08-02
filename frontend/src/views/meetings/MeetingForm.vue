<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { meetingApi } from '@/api'
import { STATUS_LABELS } from '@/api/types'
import { useConfigStore } from '@/stores/config'
import PageHeader from '@/components/PageHeader.vue'

const config = useConfigStore()
const fl = config.fieldLabel
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

// 保存并继续：新增模式下批量录入不停顿
async function onSaveAndContinue() {
  if (id || !formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      await meetingApi.create(toPayload())
      ElMessage.success('已保存，继续登记下一条')
      Object.assign(form, {
        meeting_name: '', meeting_time: '', location: '', contact_name: '',
        contact_phone: '', technicians: '', equipment: '', debug_content: '',
        problem_description: '', handling_process: '', result: '',
        onsite_support: false, status: 'pending', remark: '',
      })
      formRef.value?.clearValidate()
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <div>
    <PageHeader :title="id ? '编辑会议调试' : '新增会议调试'" description="登记会议信息、调试内容与处理结果" icon="Calendar">
      <el-button @click="router.push('/meetings')">返回列表</el-button>
    </PageHeader>

    <el-card v-loading="loading" shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="meeting-form">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'meeting_name')" prop="meeting_name">
              <el-input v-model="form.meeting_name" placeholder="请输入会议名称" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'meeting_time')">
              <el-date-picker
                v-model="form.meeting_time"
                type="datetime"
                value-format="YYYY-MM-DD HH:mm:ss"
                placeholder="选择时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'location')">
              <el-input v-model="form.location" placeholder="会议室 / 场地" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'technicians')">
              <el-input v-model="form.technicians" placeholder="多个用逗号分隔" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'contact_name')">
              <el-input v-model="form.contact_name" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'contact_phone')">
              <el-input v-model="form.contact_phone" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'status')">
              <el-select v-model="form.status" style="width: 100%">
                <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="24" :md="12">
            <el-form-item :label="fl('meetings', 'onsite_support')">
              <el-switch v-model="form.onsite_support" active-text="需要" inactive-text="不需要" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="fl('meetings', 'equipment')">
          <el-input v-model="form.equipment" type="textarea" :rows="2" placeholder="使用的设备 / 线材 / 素材" />
        </el-form-item>
        <el-form-item :label="fl('meetings', 'debug_content')">
          <el-input v-model="form.debug_content" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="fl('meetings', 'problem_description')">
          <el-input v-model="form.problem_description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="fl('meetings', 'handling_process')">
          <el-input v-model="form.handling_process" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item :label="fl('meetings', 'result')">
          <el-input v-model="form.result" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item :label="fl('meetings', 'remark')">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item>
          <el-button v-if="!id" type="primary" plain :loading="submitting" @click="onSaveAndContinue">保存并继续</el-button>
          <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
          <el-button @click="router.push('/meetings')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.meeting-form {
  max-width: 960px;
}
.meeting-form :deep(.el-form-item) {
  margin-bottom: 20px;
}
</style>
