<template>
  <div class="login-wrapper">
    <div class="login-decor-bg"></div>

    <div class="login-card-container">
      <div class="login-brand">
        <div class="brand-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="w-8 h-8">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
            <path d="M6 6h10" />
            <path d="M6 10h10" />
            <path d="M6 14h6" />
          </svg>
        </div>
        <h1 class="brand-title">企业智能考务系统</h1>
        <p class="brand-subtitle">轻量·专业·企业级统一智能考核与能力评测系统</p>
      </div>

      <div class="login-box app-card">
        <el-tabs v-model="activeTab" class="login-tabs">
          <!-- 账号密码登录 -->
          <el-tab-pane label="账号登录" name="account">
            <el-form :model="loginForm" class="mt-4" @submit.prevent="handleLogin">
              <el-form-item>
                <el-input 
                  v-model="loginForm.username" 
                  placeholder="用户名 / 工号"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
                      <circle cx="12" cy="7" r="4" />
                    </svg>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item>
                <el-input 
                  v-model="loginForm.password" 
                  type="password" 
                  placeholder="登录密码"
                  size="large"
                  show-password
                >
                  <template #prefix>
                    <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                  </template>
                </el-input>
              </el-form-item>

              <el-button 
                type="primary" 
                size="large" 
                class="w-full submit-btn" 
                :loading="loading"
                @click="handleLogin"
              >
                立即登录
              </el-button>
            </el-form>
          </el-tab-pane>

          <!-- OneAuth SSO 统一身份登录 -->
          <el-tab-pane label="OneAuth 单点登录" name="sso">
            <div class="sso-pane-content">
              <div class="sso-icon-box">
                <svg class="sso-shield" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                  <path d="m9 12 2 2 4-4" />
                </svg>
              </div>
              <h3>企业统一身份认证 (SSO)</h3>
              <p>使用企业已绑定的 OneAuth 账号免密一键登录，并自动同步所属部门架构。</p>
              
              <el-button 
                type="success" 
                size="large" 
                class="w-full sso-login-btn"
                @click="handleOneAuthRedirect"
              >
                前往 OneAuth 授权登录
              </el-button>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeTab = ref('account')
const loading = ref(false)
const loginForm = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await authApi.login(loginForm.value)
    userStore.setAuth(res.access_token, res.user)
    ElMessage.success(`欢迎回来，${res.user.full_name}`)
    if (res.user.role === 'student') {
      router.push('/student/exams')
    } else {
      router.push('/admin/analytics')
    }
  } catch (e) {
    // 错误在拦截器已提示
  } finally {
    loading.value = false
  }
}

const handleOneAuthRedirect = async () => {
  try {
    const res = await authApi.getOneAuthUrl()
    if (res.authorize_url) {
      window.location.href = res.authorize_url
    }
  } catch (e) {
    ElMessage.error('获取 SSO 授权链接失败')
  }
}

onMounted(() => {
  if (route.query.sso === 'true' || route.query.sso === '1' || route.query.from === 'oneauth') {
    handleOneAuthRedirect()
  }
})
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  position: relative;
  overflow: hidden;
  padding: 20px;
}

.login-decor-bg {
  position: absolute;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, rgba(255, 255, 255, 0) 70%);
  top: -150px;
  right: -100px;
  pointer-events: none;
}

.login-card-container {
  width: 100%;
  max-width: 440px;
  z-index: 10;
}

.login-brand {
  text-align: center;
  margin-bottom: 24px;
}

.brand-logo {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 20px -5px rgba(37, 99, 235, 0.35);
  margin-bottom: 12px;
}

.brand-title {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 6px;
}

.brand-subtitle {
  font-size: 13px;
  color: #64748b;
}

.login-box {
  padding: 32px;
  background: white;
  border-radius: 18px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
}

.input-icon {
  width: 18px;
  height: 18px;
  color: #94a3b8;
}

.submit-btn {
  margin-top: 10px;
  font-weight: 600;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  border: none;
}

.sso-pane-content {
  text-align: center;
  padding: 16px 0;
}

.sso-icon-box {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #ecfdf5;
  color: #10b981;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.sso-shield {
  width: 24px;
  height: 24px;
}

.sso-pane-content h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
}
.sso-pane-content p {
  font-size: 12.5px;
  color: #64748b;
  margin-bottom: 20px;
  line-height: 1.5;
}

.sso-login-btn {
  border-radius: 10px;
  font-weight: 600;
}
</style>
