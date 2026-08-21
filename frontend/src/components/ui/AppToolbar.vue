<template>
  <div class="app-toolbar">
    <div class="toolbar-filters"><slot /></div>
    <div v-if="$slots.actions" class="toolbar-actions"><slot name="actions" /></div>
  </div>
</template>

<style scoped>
.app-toolbar { min-height: 52px; padding: 10px var(--app-space-5); display: flex; align-items: center; justify-content: space-between; gap: var(--app-space-3); background: var(--color-fill-1); border-bottom: 1px solid var(--color-border-1); }
.toolbar-filters { min-width: 0; display: flex; align-items: center; gap: var(--app-space-2); flex-wrap: wrap; }
.toolbar-actions { flex: 0 0 auto; display: flex; align-items: center; justify-content: flex-end; gap: var(--app-space-2); flex-wrap: wrap; }
@media (max-width: 720px) {
  .app-toolbar { padding: var(--app-space-3) var(--app-space-4); align-items: stretch; flex-direction: column; }
  .toolbar-filters, .toolbar-actions { width: 100%; justify-content: flex-start; }
}
</style>
