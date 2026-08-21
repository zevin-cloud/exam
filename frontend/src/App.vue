<template>
  <a-config-provider :locale="zhCn" size="medium">
    <router-view />
  </a-config-provider>
</template>

<script setup>
import zhCn from '@arco-design/web-vue/es/locale/lang/zh-cn'
</script>

<style>
#app {
  width: 100%;
  min-height: 100vh;
}
</style>
