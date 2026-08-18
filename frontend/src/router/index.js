import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/auth/sso',
    name: 'DirectSSO',
    component: () => import('@/views/login/DirectSSO.vue'),
    meta: { public: true }
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: () => import('@/views/login/AuthCallback.vue'),
    meta: { public: true }
  },
  {
    path: '/exam/take/:id',
    name: 'ExamTaking',
    component: () => import('@/views/student/ExamTaking.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exam/result/:recordId',
    name: 'ExamResult',
    component: () => import('@/views/student/ExamResult.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardDispatcher.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/student/exams',
        name: 'StudentExams',
        component: () => import('@/views/student/ExamList.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: '/admin/analytics',
        name: 'Analytics',
        component: () => import('@/views/analytics/AnalyticsDashboard.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/questions',
        name: 'Questions',
        component: () => import('@/views/questions/QuestionBank.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/papers',
        name: 'Papers',
        component: () => import('@/views/papers/PaperList.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/papers/editor',
        name: 'PaperEditorNew',
        component: () => import('@/views/papers/PaperEditor.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/papers/editor/:id',
        name: 'PaperEditorEdit',
        component: () => import('@/views/papers/PaperEditor.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/papers/new',
        name: 'PaperCreate',
        component: () => import('@/views/papers/PaperEditor.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/papers/edit/:id',
        name: 'PaperEdit',
        component: () => import('@/views/papers/PaperEditor.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/exams',
        name: 'Exams',
        component: () => import('@/views/exams/ExamTaskList.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/grading',
        name: 'Grading',
        component: () => import('@/views/grading/GradingHub.vue'),
        meta: { requiresAuth: true, roles: ['super_admin', 'teacher'] }
      },
      {
        path: '/admin/org',
        name: 'OrgSync',
        component: () => import('@/views/organization/OrgSync.vue'),
        meta: { requiresAuth: true, roles: ['super_admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from) => {
  const userStore = useUserStore()
  if (to.meta.public) {
    return true
  }
  if (!userStore.isLoggedIn) {
    // 若请求带有 sso 相关参数，直接无感知进入单点直连
    if (to.query.sso === 'true' || to.query.sso === '1' || to.query.from === 'oneauth') {
      return { path: '/auth/sso' }
    }
    return { name: 'Login' }
  }
  // 角色权限检查
  if (to.meta.roles && !to.meta.roles.includes(userStore.role)) {
    return { path: '/student/exams' }
  }
  return true
})

export default router
