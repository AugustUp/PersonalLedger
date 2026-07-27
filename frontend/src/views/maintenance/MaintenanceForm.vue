<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { maintenanceApi, departmentApi } from '@/api'
import { STATUS_LABELS, MAINTENANCE_CATEGORY_GROUPS } from '@/api/types'
import type { DepartmentOut } from '@/api/types'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const id = route.params.id ? Number(route.params.id) : null
const departments = ref<DepartmentOut[]>([])

const form = reactive({
  category: '',
  related_system: '',
  requester: '',
  department_id: null as number | null,
  contact_phone: '',
  location: '',
  problem_description: '',
  handling_process: '',
  fault_cause: '',
  result: '',
  status: 'pending',
  handler: '',
  started_at: '' as string,
  finished_at: '' as string,
  remark: '',
})

const rules: FormRules = {
  requester: [{ required: true, message: '请输入报修人', trigger: 'blur' }],
}

const statusOptions = Object.entries(STATUS_LABELS.maintenance).map(([v, l]) => ({ value: v, label: l }))
const categoryGroups = MAINTENANCE_CATEGORY_GROUPS

function toPayload() {
  const p: Record<string, any> = { ...form }
  if (p.started_at === '') p.started_at = null
  if (p.finished_at === '') p.finished_at = null
  if (p.department_id === null) delete p.department_id
  return p
}

onMounted(async () => {
  try {
    const d = await departmentApi.list({ page_size: 200 })
    departments.value = d.items
  } catch {
    /* ignore */
  }
  if (id) {
    loading.value = true
    try {
      const d = await maintenanceApi.get(id)
      Object.assign(form, {
        category: d.category || '',
        related_system: d.related_system || '',
        requester: d.requester || '',
        department_id: d.department_id,
        contact_phone: d.contact_phone || '',
        location: d.location || '',
        problem_description: d.problem_description || '',
        handling_process: d.handling_process || '',
        fault_cause: d.fault_cause || '',
        result: d.result || '',
        status: d.status,
        handler: d.handler || '',
        started_at: d.started_at || '',
        finished_at: d.finished_at || '',
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
        await maintenanceApi.update(id, toPayload())
        ElMessage.success('更新成功')
      } else {
        await maintenanceApi.create(toPayload())
        ElMessage.success('创建成功')
      }
      router.push('/maintenance')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <el-card v-loading="loading" shadow="never">
    <template #header><span>{{ id ? '编辑维护记录' : '新增维护记录' }}</span></template>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" style="max-width: 780px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="报修人" prop="requester">
            <el-input v-model="form.requester" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="部门">
            <el-select v-model="form.department_id" placeholder="选择部门" clearable filterable style="width: 100%">
              <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话">
            <el-input v-model="form.contact_phone" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="地点">
            <el-input v-model="form.location" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="分类" prop="category">
            <el-select v-model="form.category" placeholder="选择任务分类" filterable style="width: 100%">
              <el-option-group v-for="g in categoryGroups" :key="g.label" :label="g.label">
                <el-option v-for="c in g.options" :key="c" :label="c" :value="c" />
              </el-option-group>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="关联系统/设备">
            <el-input v-model="form.related_system" placeholder="如 NCE-Campus / 深澜 / AC 型号" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="经办人">
            <el-input v-model="form.handler" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="开始时间">
            <el-date-picker v-model="form.started_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="结束时间">
            <el-date-picker v-model="form.finished_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="问题描述">
        <el-input v-model="form.problem_description" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="处理过程">
        <el-input v-model="form.handling_process" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item label="故障原因">
        <el-input v-model="form.fault_cause" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="处理结果">
        <el-input v-model="form.result" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
        <el-button @click="router.push('/maintenance')">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>
