<template>
  <div class="callback-container">
    <div class="callback-card app-card text-center p-8">
      <el-icon class="is-loading" :size="40" color="#3b82f6"><Loading /></el-icon>
      <h3 class="text-lg font-bold text-slate-800 mt-4">正在通过 OneAuth 统一身份授权...</h3>
      <p class="text-xs text-slate-500 mt-2">请稍候，系统正在同步您的部门信息与考试权限</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

onMounted(async () => {
  const code = route.query.code
  if (!code) {
    ElMessage.error('未能获取 SSO 授权凭据 Code')
    router.replace('/login')
    return
  }

  try {
    const res = await authApi.handleOneAuthCallback({ code, state: route.query.state })
    userStore.setAuth(res.access_token, res.user)
    ElMessage.success(`OneAuth SSO 登录成功！欢迎，${res.user.full_name}`)
    if (res.user.role === 'student') {
      router.replace('/student/exams')
    } else {
      router.replace('/admin/analytics')
    }
  } catch (e) {
    ElMessage.error('SSO 认证回调失败，请重试')
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
  background: #f8fafc;
}
.callback-card {
  width: 380px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
}
</style>
