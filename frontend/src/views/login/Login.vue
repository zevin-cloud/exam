<template>
  <main class="login-page">
    <section class="login-stage" aria-labelledby="login-heading">
      <div class="stage-brand">
        <div class="brand-mark" aria-hidden="true">
          <span></span><span></span><span></span>
        </div>
        <div>
          <strong>Exam Control</strong>
          <small>企业智能考务平台</small>
        </div>
      </div>

      <div class="stage-content">
        <p class="stage-kicker">ENTERPRISE ASSESSMENT</p>
        <h1 id="login-heading">让每一场考核，<br />都有清晰的进程。</h1>
        <p class="stage-intro">从题库建设到成绩分析，在一条可追踪的考务链路上完成组织培训与能力评测。</p>

        <ol class="stage-flow" aria-label="考务流程">
          <li v-for="(step, index) in flowSteps" :key="step" :class="{ active: index === 2 }">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <em>{{ step }}</em>
          </li>
        </ol>
      </div>

      <div class="stage-foot">
        <icon-safe />
        <span>OneAuth 统一身份认证</span>
      </div>
    </section>

    <section class="login-panel">
      <div class="mobile-brand">
        <div class="brand-mark" aria-hidden="true"><span></span><span></span><span></span></div>
        <strong>Exam Control</strong>
      </div>

      <div class="login-box">
        <header class="login-header">
          <span class="login-overline">欢迎使用</span>
          <h2>登录考务工作台</h2>
          <p>使用企业账号，或通过 OneAuth 安全登录。</p>
        </header>

        <a-tabs v-model:active-key="activeTab" class="login-tabs" justify>
          <a-tab-pane key="account" title="账号登录">
            <a-form :model="loginForm" layout="vertical" class="login-form" @submit-success="handleLogin">
              <a-form-item field="username" label="用户名 / 工号" hide-asterisk>
                <a-input v-model="loginForm.username" size="large" allow-clear placeholder="输入用户名或企业工号">
                  <template #prefix><icon-user /></template>
                </a-input>
              </a-form-item>
              <a-form-item field="password" label="登录密码" hide-asterisk>
                <a-input-password v-model="loginForm.password" size="large" placeholder="输入登录密码">
                  <template #prefix><icon-lock /></template>
                </a-input-password>
              </a-form-item>
              <a-button html-type="submit" type="primary" size="large" long :loading="loading">进入工作台</a-button>
            </a-form>
          </a-tab-pane>

          <a-tab-pane key="sso" title="OneAuth 单点登录">
            <div class="sso-content">
              <div class="sso-icon"><icon-safe /></div>
              <h3>企业统一身份认证</h3>
              <p>使用已绑定的 OneAuth 账号授权登录，部门和身份信息将自动同步。</p>
              <a-button type="primary" status="success" size="large" long @click="handleOneAuthRedirect">
                <template #icon><icon-launch /></template>
                前往 OneAuth 授权
              </a-button>
            </div>
          </a-tab-pane>
        </a-tabs>

        <p class="login-help"><icon-info-circle /> 首次使用请联系管理员开通组织账号</p>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { authApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const activeTab = ref('account')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const flowSteps = ['题库建设', '试卷设计', '考试发布', '智能阅卷', '数据分析']

const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    Message.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const res = await authApi.login(loginForm)
    userStore.setAuth(res.access_token, res.user)
    Message.success(`欢迎回来，${res.user.full_name}`)
    router.push(res.user.role === 'student' ? '/student/exams' : '/admin/analytics')
  } catch {
    // 统一错误由请求拦截器展示
  } finally {
    loading.value = false
  }
}

const handleOneAuthRedirect = async () => {
  try {
    const redirectUri = `${window.location.origin}/auth/callback`
    const res = await authApi.getOneAuthUrl({ redirect_uri: redirectUri })
    if (res.authorize_url) window.location.href = res.authorize_url
  } catch {
    Message.error('获取 SSO 授权链接失败')
  }
}

onMounted(() => {
  if (['true', '1'].includes(route.query.sso) || route.query.from === 'oneauth') handleOneAuthRedirect()
})
</script>

<style scoped>
.login-page { min-height: 100vh; display: grid; grid-template-columns: minmax(420px, 46%) 1fr; color: var(--color-text-1); background: var(--color-bg-2); }
.login-stage { position: relative; min-height: 100vh; padding: 42px 54px; display: flex; flex-direction: column; color: #fff; overflow: hidden; background: #165dff; }
.login-stage::before,
.login-stage::after { display: none; }
.stage-brand, .mobile-brand { position: relative; z-index: 1; display: flex; align-items: center; gap: 11px; }
.brand-mark { width: 34px; height: 34px; padding: 8px 7px; display: flex; align-items: flex-end; gap: 3px; border-radius: 7px; color: #165dff; background: #fff; }
.brand-mark span { width: 5px; border-radius: 2px 2px 1px 1px; background: currentColor; }
.brand-mark span:nth-child(1) { height: 9px; opacity: .68; }
.brand-mark span:nth-child(2) { height: 17px; }
.brand-mark span:nth-child(3) { height: 13px; opacity: .82; }
.stage-brand > div:last-child { display: flex; flex-direction: column; gap: 1px; }
.stage-brand strong { font-size: 15px; }
.stage-brand small { color: rgba(255,255,255,.7); font-size: 10px; }
.stage-content { position: relative; z-index: 1; width: min(520px, 100%); margin: auto 0; padding: 60px 0; }
.stage-kicker { margin-bottom: 16px; color: #bedaff; font-size: 10px; font-weight: 700; letter-spacing: .2em; }
.stage-content h1 { margin: 0 0 20px; color: #fff; font-size: clamp(36px, 4vw, 54px); line-height: 1.16; letter-spacing: -.045em; }
.stage-intro { max-width: 430px; color: rgba(255,255,255,.72); font-size: 14px; line-height: 1.8; }
.stage-flow { margin: 48px 0 0; padding: 0; display: flex; list-style: none; }
.stage-flow li { position: relative; flex: 1; display: flex; flex-direction: column; gap: 9px; color: rgba(255,255,255,.48); }
.stage-flow li:not(:last-child)::after { content: ''; position: absolute; top: 11px; left: 27px; right: 7px; height: 1px; background: rgba(255,255,255,.28); }
.stage-flow span { width: 23px; height: 23px; z-index: 1; display: grid; place-items: center; border: 1px solid rgba(255,255,255,.35); border-radius: 50%; font-size: 8px; background: #0e42d2; }
.stage-flow em { font-size: 10px; font-style: normal; }
.stage-flow li.active { color: #fff; }
.stage-flow li.active span { color: #0e42d2; border-color: #fff; background: #fff; box-shadow: 0 0 0 4px rgba(255,255,255,.13); }
.stage-foot { position: relative; z-index: 1; display: flex; align-items: center; gap: 7px; color: rgba(255,255,255,.62); font-size: 11px; }
.login-panel { min-height: 100vh; padding: 48px; display: grid; place-items: center; background: var(--color-bg-2); }
.mobile-brand { display: none; }
.login-box { width: min(400px, 100%); }
.login-header { margin-bottom: 28px; }
.login-overline { color: #165dff; font-size: 11px; font-weight: 700; letter-spacing: .1em; }
.login-header h2 { margin: 8px 0 10px; font-size: 27px; line-height: 1.25; letter-spacing: -.03em; }
.login-header p { color: #86909c; font-size: 13px; }
.login-tabs :deep(.arco-tabs-nav-tab) { justify-content: stretch; }
.login-tabs :deep(.arco-tabs-tab) { flex: 1; justify-content: center; }
.login-form { padding-top: 18px; }
.login-form :deep(.arco-form-item-label-col) { padding-bottom: 7px; color: #4e5969; font-size: 12px; font-weight: 600; }
.login-form :deep(.arco-input-wrapper) { border-radius: 4px; }
.login-form :deep(.arco-btn) { margin-top: 4px; font-weight: 600; }
.sso-content { padding: 32px 0 7px; text-align: center; }
.sso-icon { width: 52px; height: 52px; margin: 0 auto 14px; display: grid; place-items: center; color: #00b42a; border-radius: 50%; background: #e8ffea; font-size: 23px; }
.sso-content h3 { margin: 0 0 8px; font-size: 16px; }
.sso-content p { margin: 0 0 24px; color: #86909c; font-size: 12px; line-height: 1.65; }
.login-help { margin-top: 24px; display: flex; justify-content: center; align-items: center; gap: 6px; color: #86909c; font-size: 11px; }
@media (max-width: 900px) {
  .login-page { grid-template-columns: 1fr; }
  .login-stage { display: none; }
  .login-panel { min-height: 100vh; padding: 28px 22px; align-content: center; gap: 42px; }
  .login-box { width: 100%; min-width: 0; }
  .mobile-brand { display: flex; color: #1d2129; }
  .mobile-brand .brand-mark { color: #fff; background: #165dff; }
}
</style>
