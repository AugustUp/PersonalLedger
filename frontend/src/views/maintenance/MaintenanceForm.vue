<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { maintenanceApi, departmentApi } from '@/api'
import { STATUS_LABELS } from '@/api/types'
import { useConfigStore } from '@/stores/config'
import PageHeader from '@/components/PageHeader.vue'
import type { DepartmentOut } from '@/api/types'

const route = useRoute()
const router = useRouter()
const config = useConfigStore()
const fl = config.fieldLabel
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const id = route.params.id ? Number(route.params.id) : null
const departments = ref<DepartmentOut[]>([])

const form = reactive({
  category: '',
  related_system: '',
  requester: '',
  department_id: null as number | string | null,
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
const categoryGroups = computed(() => config.categoryGroups())

function toPayload() {
  const p: Record<string, any> = { ...form }
  if (p.started_at === '') p.started_at = null
  if (p.finished_at === '') p.finished_at = null
  // 部门：允许自由输入新名称（后端按名查找或自动创建）
  if (p.department_id === null || p.department_id === '') {
    delete p.department_id
  } else if (typeof p.department_id === 'string') {
    p.department_name = p.department_id.trim()
    delete p.department_id
  }
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
  } else {
    // 从侧边栏分组导航进入新建时，默认归类到该组第一个分类
    const g = typeof route.query.group === 'string' ? route.query.group : ''
    if (g) {
      const grp = config.categoryGroups().find((x) => x.label === g)
      if (grp && grp.options.length) form.category = grp.options[0]
    }
  }
})

const currentGroup = typeof route.query.group === 'string' && route.query.group ? (route.query.group as string) : ''
const groupQuery = currentGroup ? `?group=${encodeURIComponent(currentGroup)}` : ''

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
      router.push(`/maintenance${groupQuery}`)
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <div>
    <PageHeader
      :title="id ? '编辑维护记录' : '新增维护记录'"
      description="按账号 / 终端 / 网络 / 无线分类登记运维任务"
      icon="Tools"
    >
      <el-button @click="router.push(`/maintenance${groupQuery}`)">返回列表</el-button>
    </PageHeader>
    <el-card v-loading="loading" shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" style="max-width: 860px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'requester')" prop="requester">
            <el-input v-model="form.requester" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'department')">
            <el-select
              v-model="form.department_id"
              placeholder="选择部门或直接输入"
              clearable
              filterable
              allow-create
              default-first-option
              style="width: 100%"
            >
              <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'contact_phone')">
            <el-input v-model="form.contact_phone" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'location')">
            <el-input v-model="form.location" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'category')" prop="category">
            <el-select v-model="form.category" placeholder="选择任务分类" filterable style="width: 100%">
              <el-option-group v-for="g in categoryGroups" :key="g.label" :label="g.label">
                <el-option v-for="c in g.options" :key="c" :label="c" :value="c" />
              </el-option-group>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'related_system')">
            <el-input v-model="form.related_system" placeholder="如 NCE-Campus / 深澜 / AC 型号" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'handler')">
            <el-input v-model="form.handler" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'started_at')">
            <el-date-picker v-model="form.started_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'finished_at')">
            <el-date-picker v-model="form.finished_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('maintenance', 'status')">
            <el-select v-model="form.status" style="width: 100%">
              <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item :label="fl('maintenance', 'problem_description')">
        <el-input v-model="form.problem_description" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item :label="fl('maintenance', 'handling_process')">
        <el-input v-model="form.handling_process" type="textarea" :rows="3" />
      </el-form-item>
      <el-form-item :label="fl('maintenance', 'fault_cause')">
        <el-input v-model="form.fault_cause" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item :label="fl('maintenance', 'result')">
        <el-input v-model="form.result" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item :label="fl('maintenance', 'remark')">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
        <el-button @click="router.push(`/maintenance${groupQuery}`)">取消</el-button>
      </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>
