<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo-box">
          <svg class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
            <path d="M6 6h10" />
            <path d="M6 10h10" />
            <path d="M6 14h6" />
          </svg>
        </div>
        <div class="logo-text">
          <div class="title">Enterprise Exam</div>
          <div class="subtitle">企业智能考务平台</div>
        </div>
      </div>

      <nav class="nav-menu">
        <!-- 考生端专属 -->
        <div class="menu-group-title">学习与考试</div>
        <router-link to="/student/exams" class="nav-item" active-class="active">
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect width="18" height="18" x="3" y="3" rx="2" />
            <path d="m9 12 2 2 4-4" />
          </svg>
          <span>我的考务中心</span>
        </router-link>

        <!-- 管理/考官端 -->
        <template v-if="userStore.isTeacher || userStore.isSuperAdmin">
          <div class="menu-group-title">考务与数据中心</div>
          
          <router-link to="/admin/analytics" class="nav-item" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 3v18h18" />
              <path d="m19 9-5 5-4-4-3 3" />
            </svg>
            <span>考务分析与数据大盘</span>
          </router-link>

          <router-link to="/admin/questions" class="nav-item" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2v20" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
            <span>题库与试题管理</span>
          </router-link>

          <router-link to="/admin/papers" class="nav-item" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span>试卷设计与管理</span>
          </router-link>

          <router-link to="/admin/exams" class="nav-item" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
              <line x1="16" x2="16" y1="2" y2="6" />
              <line x1="8" x2="8" y1="2" y2="6" />
              <line x1="3" x2="21" y1="10" y2="10" />
            </svg>
            <span>考务排期与发布</span>
          </router-link>

          <router-link to="/admin/grading" class="nav-item" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
            </svg>
            <span>主观题阅卷工作台</span>
          </router-link>
        </template>

        <!-- 超管端 -->
        <template v-if="userStore.isSuperAdmin">
          <div class="menu-group-title">系统与集成</div>
          <router-link to="/admin/org" class="nav-item" active-class="active">
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
            <span>组织架构管理</span>
          </router-link>
        </template>
      </nav>

      <div class="sidebar-footer">
        <div class="sso-badge">
          <span class="status-dot"></span>
          <span>统一身份认证已连接</span>
        </div>
      </div>
    </aside>

    <!-- 主体区域 -->
    <div class="main-wrapper">
      <!-- 顶栏 -->
      <header class="top-header glass-panel">
        <div class="header-left">
          <!-- 干净简洁的顶栏左侧 -->
        </div>

        <div class="header-right">
          <el-dropdown
            trigger="click"
            placement="bottom-end"
            popper-class="account-dropdown"
            @command="handleAccountCommand"
          >
            <button class="account-trigger" type="button" aria-label="打开账户菜单">
              <div class="avatar-circle" aria-hidden="true">
                {{ userStore.fullName ? userStore.fullName.charAt(0) : 'U' }}
                <span class="avatar-status"></span>
              </div>
              <div class="user-meta">
                <span class="user-name">{{ userStore.fullName }}</span>
                <div class="identity-line">
                  <span class="role-label">{{ getRoleName(userStore.role) }}</span>
                  <span class="identity-divider" aria-hidden="true"></span>
                  <span class="dept-text">{{ userStore.deptName || '企业成员' }}</span>
                </div>
              </div>
              <ChevronDown :size="15" class="account-chevron" aria-hidden="true" />
            </button>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <LogOut :size="15" />
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区 -->
      <main class="content-body">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChevronDown, LogOut } from 'lucide-vue-next'

const userStore = useUserStore()
const router = useRouter()

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
  ElMessage.info('已退出登录')
}

const handleAccountCommand = (command) => {
  if (command === 'logout') handleLogout()
}

const getRoleName = (role) => {
  if (role === 'super_admin') return '超级管理员'
  if (role === 'teacher') return '出题/阅卷人'
  return '考生/员工'
}

</script>

<style scoped>
.layout-container {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: #f8fafc;
}

.sidebar {
  width: 260px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar-header {
  height: 64px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.logo-box {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}
.logo-icon {
  width: 20px;
  height: 20px;
}

.logo-text .title {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.3px;
}
.logo-text .subtitle {
  font-size: 11px;
  color: #64748b;
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.menu-group-title {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  padding: 12px 12px 6px 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  color: #475569;
  text-decoration: none;
  font-size: 13.5px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.nav-icon {
  width: 18px;
  height: 18px;
  color: #64748b;
  transition: color 0.15s ease;
}

.nav-item:hover {
  background: #f1f5f9;
  color: #1e293b;
}
.nav-item:hover .nav-icon {
  color: #3b82f6;
}

.nav-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
}
.nav-item.active .nav-icon {
  color: #2563eb;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #f1f5f9;
  flex-shrink: 0;
}
.sso-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #059669;
  background: #ecfdf5;
  padding: 8px 12px;
  border-radius: 8px;
  font-weight: 500;
}
.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 0 2px #a7f3d0;
}

.main-wrapper {
  flex: 1;
  height: 100vh;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.top-header {
  height: 64px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e2e8f0;
  background: #ffffff;
  flex-shrink: 0;
  z-index: 20;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.account-trigger {
  appearance: none;
  min-width: 0;
  padding: 6px 8px 6px 7px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 10px;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
}

.account-trigger:hover,
.account-trigger:focus-visible {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.account-trigger:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.14);
}

.avatar-circle {
  position: relative;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 3px 10px rgba(59, 130, 246, 0.24);
}

.avatar-status {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 9px;
  height: 9px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  background: #22c55e;
}

.user-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.user-meta .user-name {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13.5px;
  line-height: 1.2;
  font-weight: 650;
  color: #0f172a;
}

.identity-line {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  line-height: 1.2;
  color: #64748b;
}

.role-label {
  color: #2563eb;
  font-weight: 600;
  white-space: nowrap;
}

.identity-divider {
  width: 3px;
  height: 3px;
  flex: 0 0 3px;
  border-radius: 50%;
  background: #cbd5e1;
}

.user-meta .dept-text {
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-chevron {
  flex: 0 0 auto;
  color: #94a3b8;
  transition: transform 0.16s ease, color 0.16s ease;
}

.account-trigger:hover .account-chevron {
  color: #475569;
}

@media (max-width: 720px) {
  .top-header {
    padding: 0 14px;
  }

  .user-meta,
  .account-chevron {
    display: none;
  }

  .account-trigger {
    padding: 5px;
  }
}

.content-body {
  flex: 1;
  padding: 24px 28px;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
