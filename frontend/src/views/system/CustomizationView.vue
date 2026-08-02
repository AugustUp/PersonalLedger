<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useConfigStore } from '@/stores/config'
import type { CategoryGroup } from '@/api/types'
import PageHeader from '@/components/PageHeader.vue'

const store = useConfigStore()
const loading = ref(false)
const saving = ref(false)
const activeFieldModule = ref('meetings')

// ---- 字段枚举（用于字段标签 tab 渲染）----
const FIELD_MODULES: { key: string; title: string; fields: string[] }[] = [
  {
    key: 'meetings',
    title: '会议调试台账',
    fields: ['meeting_name', 'meeting_time', 'location', 'contact_name', 'contact_phone',
      'technicians', 'equipment', 'debug_content', 'problem_description',
      'handling_process', 'result', 'onsite_support', 'status', 'remark'],
  },
  {
    key: 'network_assets',
    title: 'IP/MAC 台账',
    fields: ['ip_address', 'mac_address', 'user_name', 'department', 'device_name',
      'device_type', 'building', 'room', 'vlan', 'switch_name', 'switch_port',
      'account_name', 'registered_at', 'status', 'remark'],
  },
  {
    key: 'account_batches',
    title: '批量账号台账',
    fields: ['batch_name', 'account_type', 'applicant_department', 'applicant',
      'application_date', 'handler', 'status', 'remark'],
  },
  {
    key: 'maintenance',
    title: '通用维护台账',
    fields: ['category', 'related_system', 'requester', 'department', 'contact_phone',
      'location', 'problem_description', 'handling_process', 'fault_cause', 'result',
      'status', 'handler', 'started_at', 'finished_at', 'remark'],
  },
]

// ---- 本地编辑副本 ----
const names = reactive<Record<string, string>>({})
const groups = ref<CategoryGroup[]>([])
const fields = reactive<Record<string, Record<string, { label: string }>>>({})

function init() {
  for (const m of FIELD_MODULES) {
    names[m.key] = store.ledgerName(m.key)
    fields[m.key] = {}
    for (const f of m.fields) fields[m.key][f] = { label: store.fieldLabel(m.key, f) }
  }
  groups.value = store.categoryGroups().map((g) => ({ label: g.label, options: [...g.options] }))
}

onMounted(async () => {
  loading.value = true
  try {
    await store.fetch()
  } finally {
    init()
    loading.value = false
  }
})

// ---- 分类组编辑 ----
function addGroup() {
  groups.value.push({ label: `新分组${groups.value.length + 1}`, options: [] })
}
function removeGroup(i: number) {
  groups.value.splice(i, 1)
}
function addOption(g: CategoryGroup) {
  const v = (g as any).__input || ''
  if (!v.trim()) return
  if (g.options.includes(v.trim())) {
    ElMessage.warning(`分类「${v.trim()}」已存在`)
    return
  }
  g.options.push(v.trim())
  ;(g as any).__input = ''
}
function removeOption(g: CategoryGroup, idx: number) {
  g.options.splice(idx, 1)
}

async function saveNames() {
  saving.value = true
  try {
    await store.save({ ledger_names: { ...names } })
    ElMessage.success('台账名称已保存')
  } finally {
    saving.value = false
  }
}
async function saveGroups() {
  // 空分组过滤 + 基本校验
  const clean = groups.value
    .filter((g) => g.label.trim() && g.options.length)
    .map((g) => ({ label: g.label.trim(), options: [...g.options] }))
  if (!clean.length) {
    ElMessage.warning('至少保留一个分组')
    return
  }
  saving.value = true
  try {
    await store.save({ maintenance_categories: clean })
    groups.value = clean
    ElMessage.success('维护分类已保存')
  } finally {
    saving.value = false
  }
}
async function saveFields() {
  saving.value = true
  try {
    await store.save({ field_meta: JSON.parse(JSON.stringify(fields)) })
    ElMessage.success('字段标签已保存')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div v-loading="loading">
    <PageHeader
      title="台账定制"
      description="修改台账名称、维护分类与表单字段标签（保存后全系统即时生效）"
      icon="Setting"
    />

    <el-card shadow="never">
      <el-tabs type="border-card">
        <!-- 1) 台账名称 -->
        <el-tab-pane label="台账名称">
          <el-form label-width="140px" style="max-width: 520px">
            <el-form-item v-for="m in FIELD_MODULES" :key="m.key" :label="m.title + '名称'">
              <el-input v-model="names[m.key]" :placeholder="m.title" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="saveNames">保存名称</el-button>
              <span class="tip">修改后菜单、页头、工作台展示的名称会同步更新。</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 2) 维护分类 -->
        <el-tab-pane label="维护分类">
          <div v-for="(g, gi) in groups" :key="gi" class="group-card">
            <div class="group-head">
              <el-input v-model="g.label" placeholder="分组名称" style="width: 200px" />
              <el-button text type="danger" @click="removeGroup(gi)">删除分组</el-button>
            </div>
            <div class="group-options">
              <el-tag
                v-for="(o, oi) in g.options"
                :key="oi"
                closable
                @close="removeOption(g, oi)"
                class="opt-tag"
              >
                {{ o }}
              </el-tag>
              <el-input
                v-model="(g as any).__input"
                placeholder="输入新分类后回车添加"
                size="small"
                style="width: 220px"
                @keyup.enter="addOption(g)"
              />
            </div>
          </div>
          <el-button style="margin-top: 12px" @click="addGroup">+ 新增分组</el-button>
          <div style="margin-top: 12px">
            <el-button type="primary" :loading="saving" @click="saveGroups">保存分类</el-button>
            <span class="tip">新增/删除分类不影响历史记录（历史分类名仍会原样展示）。</span>
          </div>
        </el-tab-pane>

        <!-- 3) 字段标签 -->
        <el-tab-pane label="字段标签">
          <el-tabs v-model="activeFieldModule">
            <el-tab-pane v-for="m in FIELD_MODULES" :key="m.key" :label="m.title" :name="m.key">
              <el-form label-width="160px" style="max-width: 560px">
                <el-form-item v-for="f in m.fields" :key="f" :label="`字段 ${f}`">
                  <el-input v-model="fields[m.key][f].label" :placeholder="f" />
                </el-form-item>
              </el-form>
            </el-tab-pane>
          </el-tabs>
          <el-button type="primary" :loading="saving" @click="saveFields">保存标签</el-button>
          <span class="tip">只影响展示文案，不影响数据结构和已有数据。</span>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.group-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 12px;
  background: #fafbfc;
}
.group-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.group-options {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.opt-tag {
  font-size: 13px;
}
.tip {
  margin-left: 10px;
  color: #909399;
  font-size: 12px;
}
</style>
