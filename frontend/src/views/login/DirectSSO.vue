<template>
  <div class="direct-sso-container">
    <AppState
      class="direct-sso-card"
      loading
      loading-text="正在通过 OneAuth 单点登录..."
      description="已识别企业门户身份，正在免密直连考务系统"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { authApi } from '@/api'
import { Message } from '@arco-design/web-vue'
import AppState from '@/components/ui/AppState.vue'

onMounted(async () => {
  try {
    const res = await authApi.getOneAuthUrl()
    if (res?.authorize_url) {
      window.location.replace(res.authorize_url)
    } else {
      window.location.replace('/login')
    }
  } catch (e) {
    Message.error('无法获取 OneAuth 授权地址')
    window.location.replace('/login')
  }
})
</script>

<style scoped>
.direct-sso-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-1);
}
.direct-sso-card {
  width: min(480px, calc(100vw - 28px));
}
</style>
