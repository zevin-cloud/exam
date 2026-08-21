<template>
  <AppPage class="question-bank-page">
    <AppPageHeader
      eyebrow="考务管理"
      title="题库与试题管理"
      description="统一维护题型、答案、分值与知识点标签"
    />

    <AppPanel title="题库列表" :description="`共 ${questionList.length} 题`" flush>
      <AppToolbar>
        <div class="toolbar-filters">
          <!-- 题型筛选下拉 -->
          <div class="type-select">
            <a-select
              v-model="filterType"
              placeholder="全部题型"
              allow-clear
              @change="fetchQuestions"
            >
              <a-option label="单选题" value="single_choice" />
              <a-option label="多选题" value="multi_choice" />
              <a-option label="判断题" value="true_false" />
              <a-option label="填空题" value="fill_blank" />
              <a-option label="问答/简答题" value="essay" />
            </a-select>
          </div>

          <!-- 搜索输入框 -->
          <a-input
            v-model="searchKeyword" 
            placeholder="搜索题干或知识点" 
            allow-clear
            class="search-input"
            @keyup.enter="fetchQuestions"
            @clear="fetchQuestions"
          >
            <template #prefix><icon-search /></template>
          </a-input>

        </div>
        <template #actions>
          <div class="action-btn-group">
            <a-button @click="downloadTemplate">
              下载模板
            </a-button>
            <a-button @click="openImportDialog">
              批量导入
            </a-button>
            <a-button @click="exportExcel">
              导出Excel
            </a-button>
            <a-button type="primary" class="new-btn" @click="openCreateDialog">
              <template #icon><icon-plus /></template>新建题目
            </a-button>
          </div>
        </template>
      </AppToolbar>

      <!-- 题目表格 -->
      <div class="table-wrapper">
        <a-table
          :columns="questionColumns"
          :data="questionList"
          :loading="loading"
          :pagination="false"
          row-key="id"
          class="custom-data-table"
        >
          <template #type="{ record }">
              <span class="type-pill" :class="`pill-${record.type}`">
                {{ getTypeName(record.type) }}
              </span>
          </template>
          <template #title="{ record }"><span class="question-title-text">{{ record.title }}</span></template>
          <template #answer="{ record }"><span class="answer-text">{{ formatAnswer(record) }}</span></template>
          <template #score="{ record }"><span class="score-text">{{ record.score }} 分</span></template>
          <template #knowledge="{ record }"><span class="knowledge-tag">{{ record.knowledge_tag || '通用' }}</span></template>
          <template #operations="{ record }">
              <div class="table-ops">
                <a-button type="text" size="mini" @click="openEditDialog(record)">编辑</a-button>
                <a-button type="text" status="danger" size="mini" @click="handleDelete(record.id)">删除</a-button>
              </div>
          </template>
        </a-table>
      </div>

      <!-- 分页与底部统计 -->
      <template #footer>
        <span class="footer-total">共 {{ questionList.length }} 道题目</span>
      </template>
    </AppPanel>

    <!-- 题目新建/编辑弹窗 -->
    <a-modal
      v-model:visible="dialogVisible"
      :title="isEdit ? '编辑题目' : '新建题目'" 
      width="640px"
      unmount-on-close
    >
      <a-form :model="form" :label-col-props="{ span: 4 }" :wrapper-col-props="{ span: 20 }" class="pr-4">
        <a-form-item label="题型" required>
          <a-select v-model="form.type" :disabled="isEdit" class="w-full">
            <a-option label="单选题 (Single Choice)" value="single_choice" />
            <a-option label="多选题 (Multi Choice)" value="multi_choice" />
            <a-option label="判断题 (True / False)" value="true_false" />
            <a-option label="填空题 (Fill Blank)" value="fill_blank" />
            <a-option label="问答/简答题 (Essay)" value="essay" />
          </a-select>
        </a-form-item>

        <a-form-item label="题干内容" required>
          <a-textarea v-model="form.title" :rows="3" placeholder="请输入题目题干描述..." />
        </a-form-item>

        <!-- 单选/多选题 选项配置 -->
        <template v-if="['single_choice', 'multi_choice'].includes(form.type)">
          <a-form-item label="选项配置">
            <div class="flex flex-col gap-2 w-full">
              <div v-for="(opt, idx) in form.options" :key="idx" class="flex gap-2 items-center">
                <span class="w-7 font-bold text-slate-500 text-center">{{ opt.value }}</span>
                <a-input v-model="opt.label" :placeholder="`选项 ${opt.value} 内容`" />
              </div>
            </div>
          </a-form-item>

          <a-form-item label="正确答案" required>
            <a-select
              v-model="form.answer" 
              :multiple="form.type === 'multi_choice'" 
              placeholder="选择正确选项" 
              class="w-full"
            >
              <a-option v-for="opt in form.options" :key="opt.value" :label="`${opt.value}. ${opt.label}`" :value="opt.value" />
            </a-select>
          </a-form-item>
        </template>

        <!-- 判断题 -->
        <template v-else-if="form.type === 'true_false'">
          <a-form-item label="正确答案" required>
            <a-radio-group v-model="form.answer[0]">
              <a-radio value="true">正确</a-radio>
              <a-radio value="false">错误</a-radio>
            </a-radio-group>
          </a-form-item>
        </template>

        <!-- 填空/问答 -->
        <template v-else>
          <a-form-item label="参考答案" required>
            <a-textarea v-if="form.type === 'essay'" v-model="form.answerRaw" :rows="3" placeholder="填写标准采分点" />
            <a-input v-else v-model="form.answerRaw" placeholder="多个同义词以英文逗号分隔" />
          </a-form-item>
        </template>

        <div class="grid grid-cols-2 gap-4">
          <a-form-item label="默认分值">
            <a-input-number v-model="form.score" :min="1" :max="100" />
          </a-form-item>
          <a-form-item label="难度">
            <a-select v-model="form.difficulty">
              <a-option label="简单" value="easy" />
              <a-option label="中等" value="medium" />
              <a-option label="困难" value="hard" />
            </a-select>
          </a-form-item>
        </div>

        <a-form-item label="知识点标签">
          <a-input v-model="form.knowledge_tag" placeholder="如：信息安全规范、产品业务知识" />
        </a-form-item>

        <a-form-item label="试题解析">
          <a-textarea v-model="form.analysis" :rows="2" placeholder="交卷后向考生展示的解析说明" />
        </a-form-item>
      </a-form>

      <template #footer>
        <a-button @click="dialogVisible = false">取消</a-button>
        <a-button type="primary" :loading="saving" @click="saveQuestion">保存题目</a-button>
      </template>
    </a-modal>

    <!-- Excel 批量导入弹窗 -->
    <a-modal v-model:visible="importVisible" title="Excel 批量导入题库" width="480px">
      <div class="py-2">
        <p class="text-xs text-slate-500 mb-4 leading-relaxed">
          请按照规范模板格式准备 Excel 文件（.xlsx）。如尚未下载，可点击右上角「下载模板」。
        </p>

        <a-upload
          draggable
          :auto-upload="false"
          :limit="1"
          accept=".xlsx, .xls"
          @change="handleFileChange"
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
        </a-upload>
      </div>

      <template #footer>
        <a-button @click="importVisible = false">取消</a-button>
        <a-button type="primary" :loading="importing" @click="submitImport">开始导入</a-button>
      </template>
    </a-modal>
  </AppPage>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { questionApi } from '@/api'
import { Message, Modal } from '@arco-design/web-vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppToolbar from '@/components/ui/AppToolbar.vue'

const loading = ref(false)
const saving = ref(false)
const importing = ref(false)
const questionList = ref([])
const filterType = ref('')
const searchKeyword = ref('')
const questionColumns = [
  { title: 'ID', dataIndex: 'id', width: 70, align: 'center' },
  { title: '题型', dataIndex: 'type', width: 110, align: 'center', slotName: 'type' },
  { title: '题干内容', dataIndex: 'title', minWidth: 280, ellipsis: true, tooltip: true, slotName: 'title' },
  { title: '参考正确答案', minWidth: 180, ellipsis: true, tooltip: true, slotName: 'answer' },
  { title: '分值', dataIndex: 'score', width: 90, align: 'center', slotName: 'score' },
  { title: '知识点标签', dataIndex: 'knowledge_tag', width: 150, ellipsis: true, tooltip: true, slotName: 'knowledge' },
  { title: '操作', width: 130, align: 'center', fixed: 'right', slotName: 'operations' },
]

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
    Message.warning('请输入题干内容')
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
      Message.success('题目修改成功')
    } else {
      await questionApi.createQuestion(payload)
      Message.success('题目创建成功')
    }
    dialogVisible.value = false
    fetchQuestions()
  } finally {
    saving.value = false
  }
}

const handleDelete = (id) => {
  Modal.warning({
    title: '删除确认',
    content: '确定要删除这道题目吗？',
    hideCancel: false,
    okText: '删除题目',
    onOk: async () => {
      await questionApi.deleteQuestion(id)
      Message.success('题目已删除')
      fetchQuestions()
    },
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

const handleFileChange = (_fileList, fileItem) => {
  uploadFile.value = fileItem?.file || null
}

const submitImport = async () => {
  if (!uploadFile.value) {
    Message.warning('请先选择要上传的 Excel 文件')
    return
  }

  const fd = new FormData()
  fd.append('file', uploadFile.value)

  importing.value = true
  try {
    const res = await questionApi.importExcel(fd)
    Message.success(res.message || '导入成功！')
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
  --app-page-gap: var(--app-space-4);
}

.toolbar-filters {
  display: flex;
  align-items: center;
  gap: var(--app-space-2);
  flex-wrap: wrap;
}

.type-select {
  width: 140px;
  flex: 0 0 140px;
}
.type-select :deep(.arco-select) { width: 100%; }
.search-input {
  width: 220px;
  flex: 0 0 220px;
}

.action-btn-group {
  flex: 0 0 auto;
  display: flex;
  gap: 8px;
  align-items: center;
}

@media (max-width: 760px) {
  .type-select { width: 132px; flex-basis: 132px; }
  .search-input { width: min(100%, 220px); flex: 1 1 180px; }
}
.action-btn-group .arco-btn {
  font-weight: 500;
}
.new-btn {
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
  border-radius: var(--app-radius-control);
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
  border-radius: var(--app-radius-control);
  border: 1px solid #f1f5f9;
}

.table-ops {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.footer-total {
  font-size: 12px;
  color: #64748b;
}
</style>
