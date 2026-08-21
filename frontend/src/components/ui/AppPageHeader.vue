<template>
  <header class="app-page-header">
    <div class="header-main">
      <div v-if="$slots.icon" class="header-icon"><slot name="icon" /></div>
      <div class="header-copy">
        <span v-if="eyebrow" class="header-eyebrow">{{ eyebrow }}</span>
        <div class="title-line">
          <h1>{{ title }}</h1>
          <slot name="meta" />
        </div>
        <p v-if="description">{{ description }}</p>
      </div>
    </div>
    <div v-if="$slots.actions" class="header-actions"><slot name="actions" /></div>
  </header>
</template>

<script setup>
defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' }
})
</script>

<style scoped>
.app-page-header {
  min-height: 64px;
  padding: var(--app-space-4) var(--app-space-5);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-4);
  background: var(--color-bg-2);
  border: 1px solid var(--color-border-2);
  border-radius: var(--app-radius-panel);
}
.header-main { min-width: 0; display: flex; align-items: center; gap: var(--app-space-3); }
.header-icon { width: 36px; height: 36px; flex: 0 0 36px; display: grid; place-items: center; color: rgb(var(--primary-6)); background: var(--color-primary-light-1); border-radius: var(--app-radius-panel); }
.header-copy { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.header-eyebrow { color: var(--color-text-3); font-size: 11px; font-weight: 600; letter-spacing: .06em; }
.title-line { display: flex; align-items: baseline; gap: var(--app-space-2); }
h1 { margin: 0; color: var(--color-text-1); font-size: var(--app-font-title); line-height: 1.4; font-weight: 650; }
p { margin: 0; color: var(--color-text-3); font-size: var(--app-font-caption); line-height: 1.5; }
.header-actions { flex: 0 0 auto; display: flex; align-items: center; justify-content: flex-end; gap: var(--app-space-2); flex-wrap: wrap; }
@media (max-width: 720px) {
  .app-page-header { padding: var(--app-space-3) var(--app-space-4); align-items: flex-start; flex-direction: column; }
  .header-actions { width: 100%; justify-content: flex-start; }
  h1 { font-size: 17px; }
}
</style>
