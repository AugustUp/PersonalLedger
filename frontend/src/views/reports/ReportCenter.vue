<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { reportApi, type ReportItem, type ReportSummary } from '@/api'
import { STATUS_LABELS } from '@/api/types'
import { useConfigStore } from '@/stores/config'
import StatusTag from '@/components/StatusTag.vue'
import PageHeader from '@/components/PageHeader.vue'

const config = useConfigStore()
const loading = ref(false)
const data = ref<ReportSummary | null>(null)
const range = ref('week')
const custom = ref<[string, string] | null>(null)
const copied = ref(false)

type RangePreset = { label: string; value: string; calc: () => [string, string] }
function fmt(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
function addDays(d: Date, n: number): Date {
  const x = new Date(d)
  x.setDate(x.getDate() + n)
  return x
}
function mondayOf(d: Date): Date {
  const x = new Date(d)
  const day = x.getDay() || 7
  x.setDate(x.getDate() - day + 1)
  return x
}
function lastDayOfMonth(y: number, m: number): Date {
  return new Date(y, m + 1, 0)
}

const PRESETS: RangePreset[] = [
  { label: '本周', value: 'week', calc: () => [fmt(mondayOf(new Date())), fmt(new Date())] },
  { label: '上周', value: 'lastWeek', calc: () => {
    const m = mondayOf(addDays(new Date(), -7))
    return [fmt(m), fmt(addDays(m, 6))]
  } },
  { label: '本月', value: 'month', calc: () => {
    const n = new Date()
    return [fmt(new Date(n.getFullYear(), n.getMonth(), 1)), fmt(n)]
  } },
  { label: '上月', value: 'lastMonth', calc: () => {
    const n = new Date()
    const first = new Date(n.getFullYear(), n.getMonth() - 1, 1)
    return [fmt(first), fmt(lastDayOfMonth(first.getFullYear(), first.getMonth()))]
  } },
  { label: '本季度', value: 'quarter', calc: () => {
    const n = new Date()
    const qStart = new Date(n.getFullYear(), Math.floor(n.getMonth() / 3) * 3, 1)
    return [fmt(qStart), fmt(n)]
  } },
  { label: '上半年', value: 'h1', calc: () => {
    const y = new Date().getFullYear()
    return [`${y}-01-01`, `${y}-06-30`]
  } },
  { label: '今年', value: 'year', calc: () => {
    const y = new Date().getFullYear()
    return [`${y}-01-01`, fmt(new Date())]
  } },
  { label: '去年', value: 'lastYear', calc: () => {
    const y = new Date().getFullYear() - 1
    return [`${y}-01-01`, `${y}-12-31`]
  } },
]

async function load() {
  loading.value = true
  try {
    let s: string | undefined
    let e: string | undefined
    if (range.value === 'custom' && custom.value) {
      ;[s, e] = custom.value
    } else {
      const p = PRESETS.find((x) => x.value === range.value)
      if (p) {
        ;[s, e] = p.calc()
      }
    }
    data.value = await reportApi.summary(s, e)
    copied.value = false
  } finally {
    loading.value = false
  }
}

const MODULES = [
  { key: 'meetings', titleKey: 'meetings', icon: 'Calendar', desc: '会议调试' },
  { key: 'maintenance', titleKey: 'maintenance', icon: 'Tools', desc: '通用维护' },
  { key: 'network_assets', titleKey: 'network_assets', icon: 'Connection', desc: 'IP/MAC 台账' },
  { key: 'account_batches', titleKey: 'account_batches', icon: 'Files', desc: '账号批次' },
] as const

const grandTotal = computed(() => {
  const d = data.value
  if (!d) return 0
  return MODULES.reduce((s, m) => s + (d[m.key]?.total || 0), 0)
})

function statusLabel(module: string, status: string): string {
  const map = { meetings: 'meeting', maintenance: 'maintenance', network_assets: 'network_asset', account_batches: 'account_batch' } as Record<string, string>
  return STATUS_LABELS[map[module]]?.[status] || status
}

function dateText(v: string | null): string {
  return v ? v.slice(0, 10) : ''
}

// ---- 复制 / 导出 ----
function buildText(): string {
  if (!data.value) return ''
  const d = data.value
  const lines: string[] = []
  lines.push(`工作留底汇总（${d.start} 至 ${d.end}），共 ${grandTotal.value} 条`)
  for (const m of MODULES) {
    const mod = d[m.key]
    if (!mod || !mod.total) continue
    lines.push('')
    lines.push(`【${config.ledgerName(m.titleKey)}】${mod.total} 条`)
    mod.items.forEach((it: ReportItem, i: number) => {
      const st = statusLabel(m.key, it.status)
      lines.push(`${i + 1}. ${dateText(it.occurred_at)} ${it.record_no} ${it.title}（${st}）${it.summary ? '：' + it.summary : ''}`)
    })
  }
  return lines.join('\n')
}

async function onCopy() {
  const text = buildText()
  if (!text) {
    ElMessage.warning('当前时间段暂无记录')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    ElMessage.success('已复制到剪贴板')
    setTimeout(() => (copied.value = false), 2000)
  } catch {
    // 非 secure context 兜底
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    ta.remove()
    copied.value = true
    ElMessage.success('已复制到剪贴板')
  }
}

function downloadBlob(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(a.href)
}

function onExportMarkdown() {
  const text = buildText()
  if (!text) {
    ElMessage.warning('当前时间段暂无记录')
    return
  }
  const d = data.value!
  let md = `# 工作留底汇总（${d.start} 至 ${d.end}）\n\n> 共 ${grandTotal.value} 条\n\n`
  for (const m of MODULES) {
    const mod = d[m.key]
    if (!mod || !mod.total) continue
    md += `## ${config.ledgerName(m.titleKey)}（${mod.total} 条）\n\n`
    mod.items.forEach((it: ReportItem) => {
      md += `- **${dateText(it.occurred_at)}** ${it.record_no} ${it.title}（${statusLabel(m.key, it.status)}）${it.summary ? '：' + it.summary : ''}\n`
    })
    md += '\n'
  }
  downloadBlob(md, `工作留底_${d.start}_${d.end}.md`, 'text/markdown;charset=utf-8')
}

function onExportWord() {
  const d = data.value
  if (!d || !grandTotal.value) {
    ElMessage.warning('当前时间段暂无记录')
    return
  }
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  let rows = ''
  for (const m of MODULES) {
    const mod = d[m.key]
    if (!mod || !mod.total) continue
    rows += `<tr><td colspan="4" style="background:#f2f4f7;font-weight:bold">${esc(config.ledgerName(m.titleKey))}（${mod.total} 条）</td></tr>`
    mod.items.forEach((it: ReportItem) => {
      rows += `<tr><td>${esc(dateText(it.occurred_at))}</td><td>${esc(it.record_no)}</td><td>${esc(it.title)}（${esc(statusLabel(m.key, it.status))}）</td><td>${esc(it.summary || '')}</td></tr>`
    })
  }
  const html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word"><head><meta charset="utf-8"><title>工作留底汇总</title></head><body><h2>工作留底汇总（${esc(d.start)} 至 ${esc(d.end)}）</h2><p>共 ${grandTotal.value} 条</p><table border="1" cellspacing="0" cellpadding="6" style="border-collapse:collapse;width:100%"><tr style="background:#e8eef8"><th>日期</th><th>编号</th><th>事项</th><th>说明</th></tr>${rows}</table></body></html>`
  downloadBlob(html, `工作留底_${d.start}_${d.end}.doc`, 'application/msword;charset=utf-8')
}
</script>

<template>
  <div>
    <PageHeader title="汇报中心" description="按周/月/季/半年/年汇总留底记录，一键生成汇报素材" icon="Document">
      <el-button type="primary" :loading="loading" @click="load">
        <el-icon style="margin-right: 4px"><Refresh /></el-icon>生成
      </el-button>
    </PageHeader>

    <el-card shadow="never" class="range-card">
      <el-radio-group v-model="range" @change="load">
        <el-radio-button v-for="p in PRESETS" :key="p.value" :value="p.value">{{ p.label }}</el-radio-button>
        <el-radio-button value="custom">自定义</el-radio-button>
      </el-radio-group>
      <el-date-picker
        v-if="range === 'custom'"
        v-model="custom"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="margin-left: 12px"
        @change="load"
      />
      <span v-if="data" class="range-tip">{{ data.start }} 至 {{ data.end }}，共 {{ grandTotal }} 条</span>
    </el-card>

    <template v-if="data">
      <!-- 汇总卡片 -->
      <el-row :gutter="12" style="margin-top: 14px">
        <el-col v-for="m in MODULES" :key="m.key" :xs="12" :md="6">
          <el-card shadow="never" class="mod-card">
            <div class="mod-card-body">
              <el-icon class="mod-icon"><component :is="m.icon" /></el-icon>
              <div>
                <div class="mod-name">{{ config.ledgerName(m.titleKey) }}</div>
                <div class="mod-total">{{ data[m.key].total }} 条</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 操作栏 -->
      <div class="actions">
        <el-button type="primary" plain @click="onCopy">
          <el-icon style="margin-right: 4px"><CopyDocument /></el-icon>{{ copied ? '已复制' : '复制全文' }}
        </el-button>
        <el-button @click="onExportMarkdown">
          <el-icon style="margin-right: 4px"><Download /></el-icon>导出 Markdown
        </el-button>
        <el-button @click="onExportWord">
          <el-icon style="margin-right: 4px"><Download /></el-icon>导出 Word
        </el-button>
      </div>

      <!-- 明细 -->
      <el-card v-for="m in MODULES" :key="m.key" shadow="never" class="detail-card">
        <template #header>
          <span class="card-title">{{ config.ledgerName(m.titleKey) }}（{{ data[m.key].total }} 条）</span>
        </template>
        <el-empty v-if="!data[m.key].total" :image-size="50" description="该时间段暂无记录" />
        <el-table v-else :data="data[m.key].items" size="small" border stripe>
          <el-table-column label="日期" width="110">
            <template #default="{ row }">{{ dateText(row.occurred_at) }}</template>
          </el-table-column>
          <el-table-column prop="record_no" label="编号" width="150" />
          <el-table-column prop="title" label="事项" min-width="160" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }"><StatusTag :module="m.key === 'meetings' ? 'meeting' : m.key === 'maintenance' ? 'maintenance' : m.key === 'network_assets' ? 'network_asset' : 'account_batch'" :status="row.status" /></template>
          </el-table-column>
          <el-table-column prop="summary" label="说明" min-width="180" show-overflow-tooltip />
        </el-table>
      </el-card>
    </template>

    <el-empty v-else-if="!loading" description="选择时间段后点击「生成」汇总留底记录" :image-size="80" />
  </div>
</template>

<style scoped>
.range-card :deep(.el-form-item) {
  margin-bottom: 0;
}
.range-tip {
  margin-left: 16px;
  color: #606266;
  font-size: 13px;
}
.mod-card-body {
  display: flex;
  align-items: center;
  gap: 12px;
}
.mod-icon {
  font-size: 26px;
  color: var(--el-color-primary);
}
.mod-name {
  color: #606266;
  font-size: 13px;
}
.mod-total {
  font-size: 20px;
  font-weight: 700;
}
.actions {
  margin: 14px 0;
}
.detail-card {
  margin-bottom: 14px;
}
.card-title {
  font-weight: 600;
}
</style>
