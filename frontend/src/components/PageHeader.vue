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
  width: 46px;
  height: 46px;
  border-radius: 13px;
  background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}
.ph-title {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
  line-height: 1.3;
}
.ph-desc {
  margin-top: 2px;
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.4;
}
.ph-actions {
  flex: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
