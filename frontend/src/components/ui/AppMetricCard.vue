<template>
  <article class="app-metric-card" :class="`tone-${tone}`">
    <div class="metric-copy">
      <span class="metric-label">{{ label }}</span>
      <div class="metric-value"><slot name="value">{{ value }}</slot><small v-if="unit">{{ unit }}</small></div>
      <p v-if="detail || $slots.detail"><slot name="detail">{{ detail }}</slot></p>
    </div>
    <div v-if="$slots.icon" class="metric-icon"><slot name="icon" /></div>
  </article>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  unit: { type: String, default: '' },
  detail: { type: String, default: '' },
  tone: { type: String, default: 'primary' }
})
</script>

<style scoped>
.app-metric-card { min-height: 112px; padding: var(--app-space-4) var(--app-space-5); display: flex; align-items: center; justify-content: space-between; gap: var(--app-space-4); background: var(--color-bg-2); border: 1px solid var(--color-border-2); border-radius: var(--app-radius-panel); box-shadow: var(--app-shadow-panel); }
.metric-copy { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.metric-label { color: var(--color-text-3); font-size: var(--app-font-caption); font-weight: 500; }
.metric-value { color: var(--color-text-1); font-size: 26px; line-height: 1.25; font-weight: 700; font-variant-numeric: tabular-nums; }
.metric-value small { margin-left: 5px; color: var(--color-text-3); font-size: 12px; font-weight: 500; }
p { margin: 0; color: var(--color-text-3); font-size: 11px; line-height: 1.5; }
.metric-icon { width: 40px; height: 40px; flex: 0 0 40px; display: grid; place-items: center; color: rgb(var(--primary-6)); background: var(--color-primary-light-1); border-radius: var(--app-radius-panel); }
.tone-success .metric-icon { color: rgb(var(--success-6)); background: var(--color-success-light-1); }
.tone-warning .metric-icon { color: rgb(var(--warning-6)); background: var(--color-warning-light-1); }
.tone-danger .metric-icon { color: rgb(var(--danger-6)); background: var(--color-danger-light-1); }
</style>
