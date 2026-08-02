<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  icon?: string
}>()
</script>

<template>
  <div class="page-header">
    <div class="ph-left">
      <div v-if="icon" class="ph-icon">
        <el-icon><component :is="icon" /></el-icon>
      </div>
      <div>
        <div class="ph-title">{{ title }}</div>
        <div v-if="description" class="ph-desc">{{ description }}</div>
      </div>
    </div>
    <div class="ph-actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}
.ph-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.ph-icon {
  flex: none;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
.ph-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2d3d;
  line-height: 1.3;
}
.ph-desc {
  margin-top: 2px;
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}
.ph-actions {
  flex: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
