import request from './request'

export const authApi = {
  login: (data) => request.post('/auth/login', data),
  getMe: () => request.get('/auth/me'),
  getOneAuthUrl: (params) => request.get('/auth/oneauth/url', { params }),
  handleOneAuthCallback: (data) => request.post('/auth/oneauth/callback', data),
  quickSwitch: (username) => request.post('/auth/quick-switch', { username })
}

export const userApi = {
  getDepartments: () => request.get('/users/departments'),
  createDepartment: (data) => request.post('/users/departments', data),
  updateDepartment: (id, data) => request.put(`/users/departments/${id}`, data),
  deleteDepartment: (id, params) => request.delete(`/users/departments/${id}`, { params }),
  getUsers: (params) => request.get('/users', { params }),
  createUser: (data) => request.post('/users', data),
  updateUser: (id, data) => request.put(`/users/${id}`, data),
  deleteUser: (id) => request.delete(`/users/${id}`),
  syncOneAuth: () => request.post('/users/sync-oneauth'),
  syncDepartments: () => request.post('/users/sync-departments'),
  getOneAuthCandidates: () => request.get('/users/oneauth-candidates'),
  importOneAuthUsers: (userKeys) => request.post('/users/import-oneauth-users', { user_keys: userKeys }),
  getSSOConfig: () => request.get('/users/sso-config'),
  updateSSOConfig: (data) => request.post('/users/sso-config', data),
  testSSOConfig: (data) => request.post('/users/sso-config/test', data),
  batchUpdateUserRole: (data) => request.post('/users/batch-role', data),
  batchDeleteUsers: (userIds) => request.post('/users/batch-delete', { user_ids: userIds })
}

export const questionApi = {
  getBanks: () => request.get('/questions/banks'),
  createBank: (data) => request.post('/questions/banks', data),
  getQuestions: (params) => request.get('/questions', { params }),
  createQuestion: (data) => request.post('/questions', data),
  updateQuestion: (id, data) => request.put(`/questions/${id}`, data),
  deleteQuestion: (id) => request.delete(`/questions/${id}`),
  downloadTemplateUrl: '/api/v1/questions/template/excel',
  exportExcelUrl: '/api/v1/questions/export/excel',
  importExcel: (formData, bankId) => request.post(`/questions/import/excel?bank_id=${bankId || ''}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const paperApi = {
  getPapers: (params) => request.get('/papers', { params }),
  getPaper: (id) => request.get(`/papers/${id}`),
  createPaper: (data) => request.post('/papers', data),
  updatePaper: (id, data) => request.put(`/papers/${id}`, data),
  deletePaper: (id) => request.delete(`/papers/${id}`),
  generateFromBank: (data) => request.post('/papers/generate-from-bank', data)
}

export const examApi = {
  getTasks: () => request.get('/exams'),
  getExamTasks: () => request.get('/exams'),
  createTask: (data) => request.post('/exams', data),
  createExamTask: (data) => request.post('/exams', data),
  updateTask: (id, data) => request.put(`/exams/${id}`, data),
  extendTaskTime: (id, data) => request.post(`/exams/${id}/extend`, data),
  getAbsentees: (id) => request.get(`/exams/${id}/absentees`),
  deleteTask: (id) => request.delete(`/exams/${id}`),
  startOrResumeExam: (id) => request.post(`/exams/${id}/start`),
  saveDraft: (recordId, data) => request.put(`/exams/records/${recordId}/draft`, data),
  uploadAttachment: (recordId, questionId, formData) => request.post(
    `/exams/records/${recordId}/questions/${questionId}/attachments`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  ),
  getAttachment: (attachmentId) => request.get(`/exams/attachments/${attachmentId}`, { responseType: 'blob' }),
  deleteAttachment: (attachmentId) => request.delete(`/exams/attachments/${attachmentId}`),
  submitExam: (recordId, data) => request.post(`/exams/records/${recordId}/submit`, data),
  getExamResult: (recordId) => request.get(`/exams/records/${recordId}/result`)
}

export const gradingApi = {
  getPendingItems: (params) => request.get('/grading/pending-items', { params }),
  gradeItem: (data) => request.post('/grading/grade-item', data)
}

export const analyticsApi = {
  getDashboard: (param) => {
    let params = {}
    if (param !== null && param !== undefined && (typeof param === 'number' || typeof param === 'string')) {
      params = { exam_task_id: param }
    } else if (param && typeof param === 'object') {
      params = param
    }
    return request.get('/analytics/dashboard', { params })
  },
  searchScores: (params) => request.get('/analytics/scores', { params }),
  exportScores: (params) => request.get('/analytics/scores/export', { params, responseType: 'blob' })
}
