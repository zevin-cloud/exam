<template>
  <section class="app-panel" :class="{ 'is-flush': flush, 'is-compact': compact }">
    <header v-if="title || description || $slots.extra" class="panel-header">
      <div class="panel-copy">
        <div class="panel-title-line">
          <h2 v-if="title">{{ title }}</h2>
          <slot name="meta" />
        </div>
        <p v-if="description">{{ description }}</p>
      </div>
      <div v-if="$slots.extra" class="panel-extra"><slot name="extra" /></div>
    </header>
    <div class="panel-body"><slot /></div>
    <footer v-if="$slots.footer" class="panel-footer"><slot name="footer" /></footer>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  flush: { type: Boolean, default: false },
  compact: { type: Boolean, default: false }
})
</script>

<style scoped>
.app-panel { overflow: hidden; background: var(--color-bg-2); border: 1px solid var(--color-border-2); border-radius: var(--app-radius-panel); box-shadow: var(--app-shadow-panel); }
.panel-header { min-height: 56px; padding: var(--app-space-3) var(--app-space-5); display: flex; align-items: center; justify-content: space-between; gap: var(--app-space-4); border-bottom: 1px solid var(--color-border-1); }
.panel-copy { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.panel-title-line { display: flex; align-items: baseline; gap: var(--app-space-2); }
h2 { margin: 0; color: var(--color-text-1); font-size: var(--app-font-section); line-height: 1.5; font-weight: 650; }
p { margin: 0; color: var(--color-text-3); font-size: var(--app-font-caption); line-height: 1.5; }
.panel-extra { display: flex; align-items: center; gap: var(--app-space-2); flex-wrap: wrap; }
.panel-body { padding: var(--app-space-5); }
.is-flush > .panel-body { padding: 0; }
.is-compact > .panel-body { padding: var(--app-space-4); }
.panel-footer { min-height: 52px; padding: var(--app-space-3) var(--app-space-5); display: flex; align-items: center; justify-content: flex-end; gap: var(--app-space-2); border-top: 1px solid var(--color-border-1); }
@media (max-width: 720px) {
  .panel-header { padding: var(--app-space-3) var(--app-space-4); align-items: flex-start; flex-direction: column; }
  .panel-body { padding: var(--app-space-4); }
  .panel-footer { padding: var(--app-space-3) var(--app-space-4); }
}
</style>
