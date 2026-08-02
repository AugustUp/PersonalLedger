<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { userApi, departmentApi } from '@/api'
import { fmtDateTime } from '@/utils/format'
import type { DepartmentOut, UserOut } from '@/api/types'

const loading = ref(false)
const rows = ref<UserOut[]>([])
const total = ref(0)
const departments = ref<DepartmentOut[]>([])
const keyword = ref('')
const page = reactive({ page: 1, page_size: 20 })

// dialogs
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const saving = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  id: 0,
  username: '',
  password: '',
  real_name: '',
  role: 'operator',
  department_id: null as number | string | null,
  is_active: true,
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  password: [
    {
      validator: (_r: any, v: string, cb: any) => {
        if (dialogMode.value === 'create' && (!v || v.length < 6)) cb(new Error('密码至少 6 位'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
}

// reset password
const resetVisible = ref(false)
const resetId = ref(0)
const resetPwd = ref('')
const resetSaving = ref(false)

const roleLabel: Record<string, string> = { admin: '系统管理员', manager: '运维管理员', operator: '普通运维' }

// 部门自由填写：输入的新部门名转 department_name 提交（后端按名查找或自动创建）
function normalizeDept(body: Record<string, any>): any {
  const p = { ...body }
  if (p.department_id === null || p.department_id === '') {
    delete p.department_id
  } else if (typeof p.department_id === 'string') {
    p.department_name = p.department_id.trim()
    delete p.department_id
  }
  return p
}

async function load() {
  loading.value = true
  try {
    const r = await userApi.list({ keyword: keyword.value, page: page.page, page_size: page.page_size })
    rows.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogMode.value = 'create'
  Object.assign(form, {
    id: 0, username: '', password: '', real_name: '', role: 'operator', department_id: null, is_active: true,
  })
  dialogVisible.value = true
}
function openEdit(row: UserOut) {
  dialogMode.value = 'edit'
  Object.assign(form, {
    id: row.id, username: row.username, password: '', real_name: row.real_name,
    role: row.role, department_id: row.department_id, is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (dialogMode.value === 'create') {
        const { id, ...body } = form
        await userApi.create(normalizeDept(body))
        ElMessage.success('创建成功')
      } else {
        const body: Record<string, any> = {
          real_name: form.real_name, role: form.role, department_id: form.department_id, is_active: form.is_active,
        }
        await userApi.update(form.id, normalizeDept(body))
        ElMessage.success('更新成功')
      }
      dialogVisible.value = false
      load()
    } finally {
      saving.value = false
    }
  })
}

async function openReset(row: UserOut) {
  resetId.value = row.id
  resetPwd.value = ''
  resetVisible.value = true
}
async function submitReset() {
  if (resetPwd.value.length < 6) {
    ElMessage.warning('密码至少 6 位')
    return
  }
  resetSaving.value = true
  try {
    await userApi.resetPassword(resetId.value, resetPwd.value)
    ElMessage.success('密码已重置')
    resetVisible.value = false
  } finally {
    resetSaving.value = false
  }
}

async function toggleActive(row: UserOut) {
  await userApi.update(row.id, { is_active: !row.is_active })
  ElMessage.success('已更新')
  load()
}

onMounted(async () => {
  try {
    const d = await departmentApi.list({ page_size: 200 })
    departments.value = d.items
  } catch {
    /* ignore */
  }
  load()
})
</script>

<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="用户名/姓名" style="width: 220px" clearable @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openCreate">新增用户</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="姓名" width="110" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'manager' ? 'warning' : 'info'" effect="light">
              {{ roleLabel[row.role] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department_name" label="部门" width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
              {{ row.is_active ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="openReset(row)">重置密码</el-button>
            <el-button link type="danger" @click="toggleActive(row)">
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pager"
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="page.page_size"
        :current-page="page.page"
        @current-change="(p: number) => { page.page = p; load() }"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增用户' : '编辑用户'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="dialogMode === 'edit'" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password :placeholder="dialogMode === 'edit' ? '留空不改' : '至少 6 位'" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="系统管理员" value="admin" />
            <el-option label="运维管理员" value="manager" />
            <el-option label="普通运维" value="operator" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
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
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSubmit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置密码" width="420px">
      <el-form label-width="90px">
        <el-form-item label="新密码">
          <el-input v-model="resetPwd" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetSaving" @click="submitReset">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}
.pager {
  margin-top: 14px;
  justify-content: flex-end;
}
</style>
