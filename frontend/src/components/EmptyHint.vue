<script setup lang="ts">
withDefaults(defineProps<{ text?: string }>(), { text: '暂无数据' })
</script>

<template>
  <div class="empty-hint">
    <div class="eh-icon">
      <el-icon><Document /></el-icon>
    </div>
    <p class="eh-text">{{ text }}</p>
    <div v-if="$slots.default" class="eh-action">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 36px 0;
  color: #a8abb2;
}
.eh-icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #f2f4f7;
  color: #c0c4cc;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 10px;
}
.eh-text {
  margin: 0 0 4px;
  font-size: 13px;
}
.eh-action {
  margin-top: 10px;
}
</style>
