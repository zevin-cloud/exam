<template>
  <div class="app-page" :class="{ 'is-fluid': fluid, 'is-immersive': immersive }">
    <slot />
  </div>
</template>

<script setup>
defineProps({
  fluid: { type: Boolean, default: false },
  immersive: { type: Boolean, default: false }
})
</script>

<style scoped>
.app-page {
  width: 100%;
  max-width: var(--app-content-max);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-4);
}
.app-page.is-fluid { max-width: none; }
.app-page.is-immersive { min-height: 100%; }
</style>
