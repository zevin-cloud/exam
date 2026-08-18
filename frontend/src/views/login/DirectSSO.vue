<template>
  <div class="direct-sso-container">
    <div class="direct-sso-card app-card text-center p-8">
      <el-icon class="is-loading" :size="42" color="#3b82f6"><Loading /></el-icon>
      <h3 class="text-lg font-bold text-slate-800 mt-4">正在通过 OneAuth 单点登录...</h3>
      <p class="text-xs text-slate-400 mt-2">已识别企业门户身份，正在免密直连考务系统</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { authApi } from '@/api'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

onMounted(async () => {
  try {
    const res = await authApi.getOneAuthUrl()
    if (res?.authorize_url) {
      window.location.replace(res.authorize_url)
    } else {
      window.location.replace('/login')
    }
  } catch (e) {
    ElMessage.error('无法获取 OneAuth 授权地址')
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
  background: #f8fafc;
}
.direct-sso-card {
  width: 380px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.05);
}
</style>
