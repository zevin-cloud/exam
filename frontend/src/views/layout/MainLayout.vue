<template>
  <a-layout class="exam-layout">
    <a-layout-sider
      class="exam-sider"
      :width="248"
      :collapsed-width="64"
      :collapsed="collapsed"
      breakpoint="lg"
      collapsible
      hide-trigger
      @collapse="collapsed = $event"
    >
      <div class="brand" :class="{ compact: collapsed }">
        <div class="brand-mark" aria-hidden="true">
          <span class="brand-mark-bar"></span>
          <span class="brand-mark-bar"></span>
          <span class="brand-mark-bar"></span>
        </div>
        <div v-if="!collapsed" class="brand-copy">
          <strong>Exam Control</strong>
          <span>企业智能考务平台</span>
        </div>
      </div>

      <a-menu class="exam-menu" :selected-keys="[route.path]" :collapsed="collapsed" @menu-item-click="navigate">
        <div v-if="!collapsed" class="menu-caption">学习与考试</div>
        <a-menu-item key="/student/exams">
          <template #icon><icon-check-square /></template>
          我的考务中心
        </a-menu-item>

        <template v-if="userStore.isTeacher || userStore.isSuperAdmin">
          <div v-if="!collapsed" class="menu-caption">考务与数据中心</div>
          <a-menu-item key="/admin/analytics">
            <template #icon><icon-dashboard /></template>
            数据概览
          </a-menu-item>
          <a-menu-item key="/admin/questions">
            <template #icon><icon-bulb /></template>
            题库管理
          </a-menu-item>
          <a-menu-item key="/admin/papers">
            <template #icon><icon-file /></template>
            试卷设计
          </a-menu-item>
          <a-menu-item key="/admin/exams">
            <template #icon><icon-calendar /></template>
            考试发布
          </a-menu-item>
          <a-menu-item key="/admin/grading">
            <template #icon><icon-edit /></template>
            阅卷工作台
          </a-menu-item>
        </template>

        <template v-if="userStore.isSuperAdmin">
          <div v-if="!collapsed" class="menu-caption">系统与集成</div>
          <a-menu-item key="/admin/org">
            <template #icon><icon-user-group /></template>
            组织架构
          </a-menu-item>
        </template>
      </a-menu>

      <div class="sider-bottom" :class="{ compact: collapsed }">
        <a-tooltip :content="collapsed ? `展开侧栏 · ${currentTitle}` : '收起侧栏'" position="right">
          <a-button class="collapse-button" type="text" shape="circle" @click="collapsed = !collapsed">
            <icon-menu-unfold v-if="collapsed" />
            <icon-menu-fold v-else />
          </a-button>
        </a-tooltip>
        <div v-if="!collapsed" class="sider-page-identity">
          <span>{{ currentSection }}</span>
          <strong>{{ currentTitle }}</strong>
        </div>
      </div>
    </a-layout-sider>

    <a-layout class="main-shell">
      <a-layout-header class="topbar">
        <div v-if="isAdminRoute" class="workflow-rail" aria-label="考务工作流">
          <button
            v-for="(item, index) in adminFlow"
            :key="item.path"
            type="button"
            class="flow-node"
            :class="{ active: route.path.startsWith(item.path), passed: index < currentFlowIndex }"
            @click="navigate(item.path)"
          >
            <span>{{ index + 1 }}</span>
            <em>{{ item.label }}</em>
          </button>
        </div>

        <a-dropdown trigger="click" position="br" @select="handleAccountCommand">
          <button class="account-trigger" type="button" aria-label="打开账户菜单">
            <a-avatar :size="36" class="user-avatar">{{ userInitial }}</a-avatar>
            <span class="user-copy">
              <strong>{{ userStore.fullName || '企业成员' }}</strong>
              <small>{{ roleName }} · {{ userStore.deptName || '企业成员' }}</small>
            </span>
            <icon-down class="account-chevron" />
          </button>
          <template #content>
            <a-doption value="logout">
              <template #icon><icon-export /></template>
              退出登录
            </a-doption>
          </template>
        </a-dropdown>
      </a-layout-header>

      <a-layout-content class="content-body">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)

const adminFlow = [
  { label: '题库', path: '/admin/questions' },
  { label: '组卷', path: '/admin/papers' },
  { label: '发布', path: '/admin/exams' },
  { label: '阅卷', path: '/admin/grading' },
  { label: '分析', path: '/admin/analytics' },
]

const pageMap = {
  '/student/exams': ['学习与考试', '我的考务中心'],
  '/admin/analytics': ['考务数据', '数据概览'],
  '/admin/questions': ['内容资产', '题库管理'],
  '/admin/papers': ['内容资产', '试卷设计'],
  '/admin/exams': ['考试运营', '考试发布'],
  '/admin/grading': ['考试运营', '阅卷工作台'],
  '/admin/org': ['系统设置', '组织架构'],
}

const matchedPage = computed(() => {
  const key = Object.keys(pageMap).find((path) => route.path.startsWith(path))
  return pageMap[key] || ['工作台', '企业考务']
})
const currentSection = computed(() => matchedPage.value[0])
const currentTitle = computed(() => matchedPage.value[1])
const isAdminRoute = computed(() => route.path.startsWith('/admin/') && route.path !== '/admin/org')
const currentFlowIndex = computed(() => adminFlow.findIndex((item) => route.path.startsWith(item.path)))
const userInitial = computed(() => (userStore.fullName || 'U').trim().charAt(0).toUpperCase())
const roleName = computed(() => {
  if (userStore.role === 'super_admin') return '超级管理员'
  if (userStore.role === 'teacher') return '出题 / 阅卷人'
  return '考生 / 员工'
})

const navigate = (path) => {
  if (path && path !== route.path) router.push(path)
}

const handleAccountCommand = (command) => {
  if (command !== 'logout') return
  userStore.logout()
  router.push('/login')
  Message.info('已退出登录')
}
</script>

<style scoped>
.exam-layout { width: 100vw; height: 100vh; overflow: hidden; background: var(--color-bg-1); }
.exam-sider { position: relative; z-index: 30; height: 100vh; background: #fff; border-right: 1px solid var(--border-color); box-shadow: none; }
:deep(.arco-layout-sider-children) { display: flex; flex-direction: column; }
.brand { height: 64px; flex: 0 0 64px; display: flex; align-items: center; gap: 12px; padding: 0 20px; border-bottom: 1px solid #f2f3f5; overflow: hidden; }
.brand.compact { justify-content: center; padding: 0; }
.brand-mark { width: 34px; height: 34px; flex: 0 0 34px; padding: 8px 7px; display: flex; align-items: flex-end; gap: 3px; border-radius: var(--app-radius-control); color: #fff; background: #165dff; }
.brand-mark-bar { width: 5px; border-radius: 2px 2px 1px 1px; background: currentColor; }
.brand-mark-bar:nth-child(1) { height: 9px; opacity: .68; }
.brand-mark-bar:nth-child(2) { height: 17px; }
.brand-mark-bar:nth-child(3) { height: 13px; opacity: .82; }
.brand-copy { display: flex; min-width: 0; flex-direction: column; gap: 2px; white-space: nowrap; }
.brand-copy strong { color: #1d2129; font-size: 15px; letter-spacing: -.2px; }
.brand-copy span { color: #86909c; font-size: 11px; }
.exam-menu { flex: 1; overflow-y: auto; padding: 10px 8px; border-right: 0; }
:deep(.arco-menu-inner) { padding: 0; }
:deep(.arco-menu-item) { height: 40px; margin-bottom: 2px; border-radius: 4px; color: #4e5969; font-weight: 500; }
:deep(.arco-menu-item.arco-menu-selected) { color: #165dff; background: #e8f3ff; }
:deep(.arco-menu-icon) { font-size: 17px; }
.menu-caption { height: 34px; display: flex; align-items: flex-end; padding: 0 12px 8px; color: #86909c; font-size: 11px; font-weight: 600; letter-spacing: .08em; white-space: nowrap; }
.sider-bottom { min-height: 62px; padding: 10px 12px; display: flex; align-items: center; gap: 10px; border-top: 1px solid #f2f3f5; background: #fff; }
.sider-bottom.compact { padding-inline: 0; justify-content: center; }
.sider-page-identity { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.sider-page-identity span { color: #86909c; font-size: 10px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; }
.sider-page-identity strong { overflow: hidden; color: #1d2129; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.main-shell { min-width: 0; height: 100vh; overflow: hidden; }
.topbar { position: relative; height: 64px; flex: 0 0 64px; padding: 0 24px; display: flex; align-items: center; gap: 24px; color: var(--color-text-1); background: var(--color-bg-2); border-bottom: 1px solid var(--color-border-2); }
.collapse-button { color: #4e5969; }
.workflow-rail { position: absolute; left: 50%; display: flex; align-items: center; transform: translateX(-50%); }
.flow-node { position: relative; appearance: none; padding: 0 18px 0 0; display: flex; align-items: center; gap: 6px; color: #86909c; background: transparent; border: 0; font: inherit; cursor: pointer; }
.flow-node:not(:last-child)::after { content: ''; width: 16px; height: 1px; margin-left: 6px; background: #c9cdd4; }
.flow-node span { width: 20px; height: 20px; display: grid; place-items: center; border: 1px solid #c9cdd4; border-radius: 50%; font-size: 10px; font-style: normal; }
.flow-node em { font-size: 11px; font-style: normal; white-space: nowrap; }
.flow-node:hover, .flow-node.active { color: #165dff; }
.flow-node.active span { color: #fff; border-color: #165dff; background: #165dff; box-shadow: 0 0 0 3px #e8f3ff; }
.flow-node.passed span { color: #165dff; border-color: #94bfff; background: #e8f3ff; }
.account-trigger { flex: 0 0 auto; margin-left: auto; appearance: none; min-width: 0; padding: 5px 7px; display: flex; align-items: center; gap: 10px; color: inherit; background: transparent; border: 1px solid transparent; border-radius: var(--app-radius-control); font: inherit; text-align: left; cursor: pointer; transition: .16s ease; }
.account-trigger:hover { background: #f7f8fa; border-color: #e5e6eb; }
.user-avatar { flex: 0 0 auto; color: #165dff; font-weight: 700; background: #e8f3ff; }
.user-copy { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.user-copy strong, .user-copy small { max-width: 170px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-copy strong { color: #1d2129; font-size: 13px; }
.user-copy small { color: #86909c; font-size: 10px; }
.account-chevron { color: #86909c; font-size: 12px; }
.content-body { min-width: 0; padding: 24px; overflow: auto; background: var(--color-bg-1); }
.page-fade-enter-active, .page-fade-leave-active { transition: opacity .14s ease, transform .14s ease; }
.page-fade-enter-from { opacity: 0; transform: translateY(4px); }
.page-fade-leave-to { opacity: 0; }
@media (max-width: 1180px) {
  .workflow-rail { display: none; }
}
@media (max-width: 720px) {
  .topbar { padding: 0 12px; gap: 8px; }
  .user-copy, .account-chevron { display: none; }
  .content-body { padding: 14px; }
}
</style>
