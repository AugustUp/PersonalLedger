<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import { networkAssetApi, departmentApi } from '@/api'
import { STATUS_LABELS } from '@/api/types'
import { useConfigStore } from '@/stores/config'
import PageHeader from '@/components/PageHeader.vue'
import type { DepartmentOut } from '@/api/types'

const config = useConfigStore()
const fl = config.fieldLabel
const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const submitting = ref(false)
const id = route.params.id ? Number(route.params.id) : null
const departments = ref<DepartmentOut[]>([])

const form = reactive({
  ip_address: '',
  mac_address: '',
  user_name: '',
  department_id: null as number | string | null,
  device_name: '',
  device_type: '',
  building: '',
  room: '',
  vlan: '',
  switch_name: '',
  switch_port: '',
  account_name: '',
  status: 'active',
  registered_at: '' as string,
  remark: '',
  change_reason: '',
})

const rules: FormRules = {
  ip_address: [{ required: true, message: '请输入 IP 地址', trigger: 'blur' }],
  mac_address: [{ required: true, message: '请输入 MAC 地址', trigger: 'blur' }],
  change_reason: [
    {
      validator: (_r: any, v: string, cb: any) => {
        if (id && !v) cb(new Error('修改必须填写修改原因'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

const statusOptions = Object.entries(STATUS_LABELS.network_asset).map(([v, l]) => ({ value: v, label: l }))

function toPayload() {
  const p: Record<string, any> = { ...form }
  if (p.registered_at === '') p.registered_at = null
  // 部门：允许自由输入新名称（后端按名查找或自动创建）
  if (p.department_id === null || p.department_id === '') {
    delete p.department_id
  } else if (typeof p.department_id === 'string') {
    p.department_name = p.department_id.trim()
    delete p.department_id
  }
  if (!id) delete p.change_reason
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
      const d = await networkAssetApi.get(id)
      Object.assign(form, {
        ip_address: d.ip_address || '',
        mac_address: d.mac_address || '',
        user_name: d.user_name || '',
        department_id: d.department_id,
        device_name: d.device_name || '',
        device_type: d.device_type || '',
        building: d.building || '',
        room: d.room || '',
        vlan: d.vlan || '',
        switch_name: d.switch_name || '',
        switch_port: d.switch_port || '',
        account_name: d.account_name || '',
        status: d.status,
        registered_at: d.registered_at || '',
        remark: d.remark || '',
        change_reason: '',
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
        await networkAssetApi.update(id, toPayload())
        ElMessage.success('更新成功')
      } else {
        await networkAssetApi.create(toPayload())
        ElMessage.success('创建成功')
      }
      router.push('/network-assets')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<template>
  <div>
    <PageHeader
      :title="id ? '编辑 IP/MAC 记录' : '新增 IP/MAC 记录'"
      description="登记终端 IP、MAC、使用人及网络接入信息"
      icon="Connection"
    >
      <el-button @click="router.push('/network-assets')">返回列表</el-button>
    </PageHeader>
    <el-card v-loading="loading" shadow="never">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" style="max-width: 860px">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'ip_address')" prop="ip_address">
            <el-input v-model="form.ip_address" placeholder="如 192.168.1.10" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'mac_address')" prop="mac_address">
            <el-input v-model="form.mac_address" placeholder="如 AA:BB:CC:DD:EE:FF" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'user_name')">
            <el-input v-model="form.user_name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'department')">
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
          <el-form-item :label="fl('network_assets', 'device_name')">
            <el-input v-model="form.device_name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'device_type')">
            <el-input v-model="form.device_type" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'building')">
            <el-input v-model="form.building" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'room')">
            <el-input v-model="form.room" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'vlan')">
            <el-input v-model="form.vlan" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'switch_name')">
            <el-input v-model="form.switch_name" placeholder="交换机名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'switch_port')">
            <el-input v-model="form.switch_port" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'account_name')">
            <el-input v-model="form.account_name" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'registered_at')">
            <el-date-picker v-model="form.registered_at" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="fl('network_assets', 'status')">
            <el-select v-model="form.status" style="width: 100%">
              <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item :label="fl('network_assets', 'remark')">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item v-if="id" label="修改原因" prop="change_reason">
        <el-input v-model="form.change_reason" type="textarea" :rows="2" placeholder="必填，用于变更历史记录" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="onSubmit">保存</el-button>
        <el-button @click="router.push('/network-assets')">取消</el-button>
      </el-form-item>
    </el-form>
    </el-card>
  </div>
</template>
