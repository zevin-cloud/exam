<template>
  <div class="callback-container">
    <AppState
      class="callback-card"
      loading
      loading-text="正在通过 OneAuth 统一身份授权..."
      description="请稍候，系统正在同步您的部门信息与考试权限"
    />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'
import { Message } from '@arco-design/web-vue'
import AppState from '@/components/ui/AppState.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  const code = route.query.code
  if (!code) {
    Message.error('未能获取 SSO 授权凭据 Code')
    router.replace('/login')
    return
  }

  try {
    const dynamicRedirectUri = `${window.location.origin}/auth/callback`
    const res = await authApi.handleOneAuthCallback({ 
      code, 
      state: route.query.state,
      redirect_uri: dynamicRedirectUri 
    })
    userStore.setAuth(res.access_token, res.user)
    Message.success(`OneAuth SSO 登录成功！欢迎，${res.user.full_name}`)
    if (res.user.role === 'student') {
      router.replace('/student/exams')
    } else {
      router.replace('/admin/analytics')
    }
  } catch (e) {
    Message.error('SSO 认证回调失败，请重试')
    router.replace('/login')
  }
})
</script>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-1);
}
.callback-card {
  width: min(480px, calc(100vw - 28px));
}
</style>
