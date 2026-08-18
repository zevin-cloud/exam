import { defineStore } from 'pinia'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('exam_token') || '',
    user: JSON.parse(localStorage.getItem('exam_user') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    role: (state) => state.user?.role || 'student',
    isSuperAdmin: (state) => state.user?.role === 'super_admin',
    isTeacher: (state) => state.user?.role === 'teacher' || state.user?.role === 'super_admin',
    isStudent: (state) => state.user?.role === 'student',
    fullName: (state) => state.user?.full_name || '未知用户',
    deptName: (state) => state.user?.department_name || '未分配部门',
  },
  actions: {
    setAuth(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('exam_token', token)
      localStorage.setItem('exam_user', JSON.stringify(user))
    },
    async quickSwitch(username) {
      const res = await authApi.quickSwitch(username)
      this.setAuth(res.access_token, res.user)
      return res.user
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('exam_token')
      localStorage.removeItem('exam_user')
    }
  }
})
