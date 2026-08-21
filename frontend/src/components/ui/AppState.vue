<template>
  <div class="app-state">
    <a-spin v-if="loading" :size="32" />
    <a-result v-else :status="status" :title="title" :subtitle="description">
      <template v-if="$slots.icon" #icon><slot name="icon" /></template>
      <template v-if="$slots.actions" #extra><slot name="actions" /></template>
    </a-result>
    <p v-if="loading">{{ loadingText }}</p>
    <small v-if="loading && description">{{ description }}</small>
  </div>
</template>

<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  loadingText: { type: String, default: '正在加载数据...' },
  status: { type: String, default: 'info' },
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.app-state { min-height: 180px; padding: var(--app-space-6); display: flex; align-items: center; justify-content: center; flex-direction: column; gap: var(--app-space-2); color: var(--color-text-3); text-align: center; }
p { margin: 0; font-size: var(--app-font-body); }
small { color: var(--color-text-3); font-size: var(--app-font-caption); }
</style>
