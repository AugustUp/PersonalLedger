<script setup lang="ts">
import { computed } from 'vue'
import { STATUS_LABELS } from '@/api/types'

const props = defineProps<{ module: string; status: string }>()

const label = computed(() => STATUS_LABELS[props.module]?.[props.status] ?? props.status)

// Element Plus tag type per status (Chinese convention: 涨红 in charts, but
// operational status uses semantic colors here).
const typeMap: Record<string, 'success' | 'info' | 'warning' | 'danger' | 'primary'> = {
  pending: 'warning',
  debugged: 'info',
  supporting: 'primary',
  completed: 'success',
  cancelled: 'info',
  active: 'success',
  inactive: 'info',
  replaced: 'danger',
  draft: 'info',
  processing: 'primary',
  partial: 'warning',
  success: 'success',
  failed: 'danger',
  skipped: 'warning',
  resolved: 'success',
  unresolved: 'danger',
  closed: 'info',
}

const type = computed(() => typeMap[props.status] ?? 'info')
</script>

<template>
  <el-tag :type="type" effect="light" size="small">{{ label }}</el-tag>
</template>
