<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox, FormInstance, FormRules } from 'element-plus'
import { departmentApi } from '@/api'
import { fmtDateTime } from '@/utils/format'
import type { DepartmentOut } from '@/api/types'

const loading = ref(false)
const rows = ref<DepartmentOut[]>([])
const total = ref(0)
const keyword = ref('')
const page = reactive({ page: 1, page_size: 50 })

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({ id: 0, name: '', code: '', parent_id: null as number | null, remark: '' })

const rules: FormRules = {
  name: [{ required: true, message: '请输入部门名称', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const r = await departmentApi.list({ keyword: keyword.value, page: page.page, page_size: page.page_size })
    rows.value = r.items
    total.value = r.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, { id: 0, name: '', code: '', parent_id: null, remark: '' })
  dialogVisible.value = true
}
function openEdit(row: DepartmentOut) {
  Object.assign(form, { id: row.id, name: row.name, code: row.code || '', parent_id: row.parent_id, remark: row.remark || '' })
  dialogVisible.value = true
}
async function onSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      if (form.id) await departmentApi.update(form.id, { ...form })
      else await departmentApi.create({ ...form })
      ElMessage.success('已保存')
      dialogVisible.value = false
      load()
    } finally {
      saving.value = false
    }
  })
}
async function onDelete(row: DepartmentOut) {
  try {
    await ElMessageBox.confirm(`确认删除部门「${row.name}」？`, '提示', { type: 'warning' })
  } catch {
    return
  }
  await departmentApi.remove(row.id)
  ElMessage.success('已删除')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <el-card shadow="never">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="部门名称" style="width: 220px" clearable @keyup.enter="load" />
        <el-button type="primary" @click="load">查询</el-button>
        <el-button type="success" @click="openCreate">新增部门</el-button>
      </div>

      <el-table :data="rows" v-loading="loading" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="user_count" label="用户数" width="90" />
        <el-table-column prop="remark" label="备注" min-width="140" show-overflow-tooltip />
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="onDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" title="部门信息" width="440px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSubmit">保存</el-button>
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
