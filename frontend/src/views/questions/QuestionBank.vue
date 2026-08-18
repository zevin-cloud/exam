<template>
  <div class="question-bank-page">
    <!-- 面包屑 -->
    <div class="breadcrumb-header">
      <div class="header-path">
        <span>考务管理</span>
        <span class="sep">/</span>
        <span class="active-path">题库与试题管理</span>
      </div>
    </div>

    <!-- 一体化专业卡片 -->
    <div class="bank-card app-card">
      <!-- 顶部工具栏 -->
      <div class="card-toolbar">
        <div class="toolbar-left">
          <h3 class="card-title">题库列表</h3>
          <span class="count-badge">共 {{ questionList.length }} 题</span>
        </div>

        <div class="toolbar-right">
          <!-- 题型筛选下拉 -->
          <el-select 
            v-model="filterType" 
            placeholder="全部题型" 
            clearable 
            class="type-select"
            @change="fetchQuestions"
          >
            <el-option label="单选题" value="single_choice" />
            <el-option label="多选题" value="multi_choice" />
            <el-option label="判断题" value="true_false" />
            <el-option label="填空题" value="fill_blank" />
            <el-option label="问答/简答题" value="essay" />
          </el-select>

          <!-- 搜索输入框 -->
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索题干或知识点" 
            clearable 
            class="search-input"
            @keyup.enter="fetchQuestions"
            @clear="fetchQuestions"
          >
            <template #prefix>
              <svg class="w-4 h-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </template>
          </el-input>

          <!-- 操作按钮组 -->
          <div class="action-btn-group">
            <el-button @click="downloadTemplate">
              下载模板
            </el-button>
            <el-button @click="openImportDialog">
              批量导入
            </el-button>
            <el-button @click="exportExcel">
              导出Excel
            </el-button>
            <el-button type="primary" class="new-btn" @click="openCreateDialog">
              + 新建题目
            </el-button>
          </div>
        </div>
      </div>

      <!-- 题目表格 -->
      <div class="table-wrapper">
        <el-table 
          :data="questionList" 
          v-loading="loading" 
          style="width: 100%"
          class="custom-data-table"
        >
          <el-table-column prop="id" label="ID" width="70" align="center" />
          
          <el-table-column label="题型" width="110" align="center">
            <template #default="{ row }">
              <span class="type-pill" :class="`pill-${row.type}`">
                {{ getTypeName(row.type) }}
              </span>
            </template>
          </el-table-column>

          <el-table-column prop="title" label="题干内容" min-width="280" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="question-title-text">{{ row.title }}</span>
            </template>
          </el-table-column>

          <el-table-column label="参考正确答案" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="answer-text">{{ formatAnswer(row) }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="score" label="分值" width="90" align="center">
            <template #default="{ row }">
              <span class="score-text">{{ row.score }} 分</span>
            </template>
          </el-table-column>

          <el-table-column prop="knowledge_tag" label="知识点标签" width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="knowledge-tag">{{ row.knowledge_tag || '通用' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="130" align="center" fixed="right">
            <template #default="{ row }">
              <div class="table-ops">
                <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDelete(row.id)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页与底部统计 -->
      <div class="card-footer">
        <span class="footer-total">共 {{ questionList.length }} 道题目</span>
      </div>
    </div>

    <!-- 题目新建/编辑弹窗 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑题目' : '新建题目'" 
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" label-width="90px" class="pr-4">
        <el-form-item label="题型" required>
          <el-select v-model="form.type" :disabled="isEdit" class="w-full">
            <el-option label="单选题 (Single Choice)" value="single_choice" />
            <el-option label="多选题 (Multi Choice)" value="multi_choice" />
            <el-option label="判断题 (True / False)" value="true_false" />
            <el-option label="填空题 (Fill Blank)" value="fill_blank" />
            <el-option label="问答/简答题 (Essay)" value="essay" />
          </el-select>
        </el-form-item>

        <el-form-item label="题干内容" required>
          <el-input v-model="form.title" type="textarea" :rows="3" placeholder="请输入题目题干描述..." />
        </el-form-item>

        <!-- 单选/多选题 选项配置 -->
        <template v-if="['single_choice', 'multi_choice'].includes(form.type)">
          <el-form-item label="选项配置">
            <div class="flex flex-col gap-2 w-full">
              <div v-for="(opt, idx) in form.options" :key="idx" class="flex gap-2 items-center">
                <span class="w-7 font-bold text-slate-500 text-center">{{ opt.value }}</span>
                <el-input v-model="opt.label" :placeholder="`选项 ${opt.value} 内容`" />
              </div>
            </div>
          </el-form-item>

          <el-form-item label="正确答案" required>
            <el-select 
              v-model="form.answer" 
              :multiple="form.type === 'multi_choice'" 
              placeholder="选择正确选项" 
              class="w-full"
            >
              <el-option v-for="opt in form.options" :key="opt.value" :label="`${opt.value}. ${opt.label}`" :value="opt.value" />
            </el-select>
          </el-form-item>
        </template>

        <!-- 判断题 -->
        <template v-else-if="form.type === 'true_false'">
          <el-form-item label="正确答案" required>
            <el-radio-group v-model="form.answer[0]">
              <el-radio label="true">正确</el-radio>
              <el-radio label="false">错误</el-radio>
            </el-radio-group>
          </el-form-item>
        </template>

        <!-- 填空/问答 -->
        <template v-else>
          <el-form-item label="参考答案" required>
            <el-input 
              v-model="form.answerRaw" 
              :type="form.type === 'essay' ? 'textarea' : 'text'"
              :rows="3"
              placeholder="填空题支持多个同义词以英文逗号分隔；问答题填写标准采分点" 
            />
          </el-form-item>
        </template>

        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="默认分值">
            <el-input-number v-model="form.score" :min="1" :max="100" />
          </el-form-item>
          <el-form-item label="难度">
            <el-select v-model="form.difficulty">
              <el-option label="简单" value="easy" />
              <el-option label="中等" value="medium" />
              <el-option label="困难" value="hard" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="知识点标签">
          <el-input v-model="form.knowledge_tag" placeholder="如：信息安全规范、产品业务知识" />
        </el-form-item>

        <el-form-item label="试题解析">
          <el-input v-model="form.analysis" type="textarea" :rows="2" placeholder="交卷后向考生展示的解析说明" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveQuestion">保存题目</el-button>
      </template>
    </el-dialog>

    <!-- Excel 批量导入弹窗 -->
    <el-dialog v-model="importVisible" title="Excel 批量导入题库" width="480px">
      <div class="py-2">
        <p class="text-xs text-slate-500 mb-4 leading-relaxed">
          请按照规范模板格式准备 Excel 文件（.xlsx）。如尚未下载，可点击右上角「下载模板」。
        </p>

        <el-upload
          drag
          action="#"
          :auto-upload="false"
          :on-change="handleFileChange"
          :limit="1"
          accept=".xlsx, .xls"
        >
          <div class="py-6 text-center">
            <svg class="w-10 h-10 text-blue-500 mx-auto mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" x2="12" y1="3" y2="15" />
            </svg>
            <div class="text-sm font-medium text-slate-700">点击或将 Excel 文件拖拽到此处</div>
            <div class="text-xs text-slate-400 mt-1">支持 5 种题型批量入库与校验</div>
          </div>
        </el-upload>
      </div>

      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="submitImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { questionApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
const questionList = ref([])
const filterType = ref('')
const searchKeyword = ref('')

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const importVisible = ref(false)
const uploadFile = ref(null)

const form = ref({
  type: 'single_choice',
  title: '',
  options: [
    { label: '', value: 'A' },
    { label: '', value: 'B' },
    { label: '', value: 'C' },
    { label: '', value: 'D' }
  ],
  answer: 'A',
  answerRaw: '',
  score: 10,
  difficulty: 'medium',
  knowledge_tag: '通用知识',
  analysis: ''
})

const fetchQuestions = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterType.value) params.type = filterType.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const res = await questionApi.getQuestions(params)
    questionList.value = res
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  isEdit.value = false
  editId.value = null
  form.value = {
    type: 'single_choice',
    title: '',
    options: [
      { label: '', value: 'A' },
      { label: '', value: 'B' },
      { label: '', value: 'C' },
      { label: '', value: 'D' }
    ],
    answer: 'A',
    answerRaw: '',
    score: 10,
    difficulty: 'medium',
    knowledge_tag: '通用基础',
    analysis: ''
  }
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  let ans = row.answer
  let ansRaw = ''
  if (['single_choice'].includes(row.type)) {
    ans = row.answer[0] || 'A'
  } else if (['fill_blank', 'essay'].includes(row.type)) {
    ansRaw = row.answer.join(', ')
  }
  form.value = {
    type: row.type,
    title: row.title,
    options: row.options?.length ? row.options : [
      { label: '', value: 'A' },
      { label: '', value: 'B' },
      { label: '', value: 'C' },
      { label: '', value: 'D' }
    ],
    answer: ans,
    answerRaw: ansRaw,
    score: row.score,
    difficulty: row.difficulty,
    knowledge_tag: row.knowledge_tag,
    analysis: row.analysis
  }
  dialogVisible.value = true
}

const saveQuestion = async () => {
  if (!form.value.title) {
    ElMessage.warning('请输入题干内容')
    return
  }

  saving.value = true
  try {
    let finalAnswer = []
    if (['single_choice'].includes(form.value.type)) {
      finalAnswer = Array.isArray(form.value.answer) ? form.value.answer : [form.value.answer]
    } else if (['multi_choice'].includes(form.value.type)) {
      finalAnswer = form.value.answer
    } else if (['true_false'].includes(form.value.type)) {
      finalAnswer = Array.isArray(form.value.answer) ? form.value.answer : [form.value.answer]
    } else {
      finalAnswer = form.value.answerRaw.split(',').map(s => s.trim()).filter(Boolean)
    }

    const payload = {
      type: form.value.type,
      title: form.value.title,
      options: ['single_choice', 'multi_choice'].includes(form.value.type) ? form.value.options : [],
      answer: finalAnswer,
      score: form.value.score,
      difficulty: form.value.difficulty,
      knowledge_tag: form.value.knowledge_tag,
      analysis: form.value.analysis
    }

    if (isEdit.value) {
      await questionApi.updateQuestion(editId.value, payload)
      ElMessage.success('题目修改成功')
    } else {
      await questionApi.createQuestion(payload)
      ElMessage.success('题目创建成功')
    }
    dialogVisible.value = false
    fetchQuestions()
  } finally {
    saving.value = false
  }
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定要删除这道题目吗？', '删除确认', {
    type: 'warning'
  }).then(async () => {
    await questionApi.deleteQuestion(id)
    ElMessage.success('题目已删除')
    fetchQuestions()
  })
}

// 导入导出
const downloadTemplate = () => {
  window.open(questionApi.downloadTemplateUrl, '_blank')
}

const exportExcel = () => {
  window.open(questionApi.exportExcelUrl, '_blank')
}

const openImportDialog = () => {
  uploadFile.value = null
  importVisible.value = true
}

const handleFileChange = (file) => {
  uploadFile.value = file.raw
}

const submitImport = async () => {
  if (!uploadFile.value) {
    ElMessage.warning('请先选择要上传的 Excel 文件')
    return
  }

  const fd = new FormData()
  fd.append('file', uploadFile.value)

  importing.value = true
  try {
    const res = await questionApi.importExcel(fd)
    ElMessage.success(res.message || '导入成功！')
    importVisible.value = false
    fetchQuestions()
  } finally {
    importing.value = false
  }
}

const formatAnswer = (row) => {
  if (!row.answer) return '-'
  if (row.type === 'true_false') return row.answer.includes('true') ? '正确' : '错误'
  return row.answer.join(', ')
}

const getTypeName = (type) => {
  const map = {
    single_choice: '单选题',
    multi_choice: '多选题',
    true_false: '判断题',
    fill_blank: '填空题',
    essay: '问答题'
  }
  return map[type] || type
}

onMounted(() => {
  fetchQuestions()
})
</script>

<style scoped>
.question-bank-page {
  max-width: 1360px;
  margin: 0 auto;
}

/* 面包屑 */
.breadcrumb-header {
  margin-bottom: 16px;
}
.header-path {
  font-size: 13px;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 8px;
}
.sep {
  color: #cbd5e1;
}
.active-path {
  color: #0f172a;
  font-weight: 600;
}

/* 主体卡片 */
.bank-card {
  background: white;
  padding: 20px 24px;
  border-radius: 14px;
  overflow: hidden;
}

/* 顶部一体化工具栏 */
.card-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-shrink: 0;
}
.card-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}
.count-badge {
  font-size: 12px;
  color: #94a3b8;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.type-select {
  width: 130px;
}
.search-input {
  width: 220px;
}

.action-btn-group {
  display: flex;
  gap: 8px;
  align-items: center;
}
.action-btn-group .el-button {
  font-weight: 500;
}
.new-btn {
  border-radius: 6px;
  font-weight: 600;
}

/* 表格内字段样式 */
.question-title-text {
  font-weight: 600;
  color: #1e293b;
  font-size: 13.5px;
}
.answer-text {
  color: #059669;
  font-weight: 600;
  font-size: 13px;
}
.score-text {
  font-size: 13px;
  color: #475569;
}

/* 题型胶囊标签 */
.type-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.pill-single_choice { background: #eff6ff; color: #2563eb; }
.pill-multi_choice  { background: #ecfdf5; color: #059669; }
.pill-true_false    { background: #fffbeb; color: #d97706; }
.pill-fill_blank    { background: #f1f5f9; color: #475569; }
.pill-essay         { background: #fef2f2; color: #dc2626; }

.knowledge-tag {
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid #f1f5f9;
}

.table-ops {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f1f5f9;
}
.footer-total {
  font-size: 12px;
  color: #64748b;
}
</style>
