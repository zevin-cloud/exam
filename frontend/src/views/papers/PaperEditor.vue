<template>
  <div class="paper-editor-layout">
    <!-- 顶栏操作栏 -->
    <header class="editor-header glass-panel">
      <div class="header-left">
        <el-button link @click="goBack">
          <svg class="w-4 h-4 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          返回列表
        </el-button>
        <div class="h-4 w-px bg-slate-200 mx-2"></div>
        <input 
          v-model="paperForm.title" 
          class="paper-title-input" 
          placeholder="请输入试卷标题（如：2026年企业合规考核试卷）..." 
        />
      </div>

      <div class="header-right">
        <div class="score-summary">
          <span>总分: <strong class="text-blue-600 font-bold text-base">{{ calculatedTotalScore }}</strong> 分</span>
          <span class="text-slate-300">|</span>
          <span>题目数: <strong class="text-slate-700">{{ elements.length }}</strong> 题</span>
        </div>
        <el-button type="primary" :loading="saving" @click="savePaper">
          保存试卷
        </el-button>
      </div>
    </header>

    <!-- 三栏编辑器工作区 -->
    <div class="editor-workspace">
      <!-- 左侧：题型工具箱 -->
      <aside class="toolbox-panel app-card">
        <div class="panel-title flex items-center">
          <LayoutGrid :size="16" class="text-blue-600 mr-1.5" /> 题目组件库
        </div>
        <p class="panel-subtitle">点击添加至试卷画布</p>

        <div class="tools-grid">
          <button class="tool-btn" @click="addQuestion('Radio')">
            <span class="tool-icon radio-icon">
              <CircleDot :size="16" class="text-blue-500" />
            </span>
            <div class="tool-info">
              <span class="name">单选题</span>
              <span class="desc">Radio</span>
            </div>
          </button>

          <button class="tool-btn" @click="addQuestion('Checkbox')">
            <span class="tool-icon check-icon">
              <CheckSquare :size="16" class="text-indigo-500" />
            </span>
            <div class="tool-info">
              <span class="name">多选题</span>
              <span class="desc">Checkbox</span>
            </div>
          </button>

          <button class="tool-btn" @click="addQuestion('TrueFalse')">
            <span class="tool-icon tf-icon">
              <Scale :size="16" class="text-amber-500" />
            </span>
            <div class="tool-info">
              <span class="name">判断题</span>
              <span class="desc">True / False</span>
            </div>
          </button>

          <button class="tool-btn" @click="addQuestion('FillBlank')">
            <span class="tool-icon fill-icon">
              <FileEdit :size="16" class="text-emerald-500" />
            </span>
            <div class="tool-info">
              <span class="name">填空题</span>
              <span class="desc">Fill Blank</span>
            </div>
          </button>

          <button class="tool-btn" @click="addQuestion('Textarea')">
            <span class="tool-icon essay-icon">
              <FileText :size="16" class="text-purple-500" />
            </span>
            <div class="tool-info">
              <span class="name">问答/简答题</span>
              <span class="desc">Essay (人工阅卷)</span>
            </div>
          </button>
        </div>
      </aside>

      <!-- 中间：试卷画布 (Canvas) -->
      <main class="canvas-area">
        <div v-if="elements.length === 0" class="canvas-empty app-card text-center py-24">
          <Palette :size="48" class="text-slate-300 mx-auto mb-2" />
          <h4 class="text-base font-bold text-slate-700">试卷画布为空</h4>
          <p class="text-xs text-slate-400 mt-1">从左侧点击添加题目组件，开始设计您的试卷</p>
        </div>

        <div v-else class="elements-list">
          <div 
            v-for="(elem, index) in elements" 
            :key="elem.id"
            class="canvas-card app-card"
            :class="{ 'is-selected': selectedElem?.id === elem.id }"
            @click="selectElement(elem)"
          >
            <div class="card-toolbar">
              <div class="flex items-center gap-2">
                <span class="elem-index">{{ index + 1 }}</span>
                <el-tag size="small" :type="getTypeTag(elem.type)">{{ getTypeName(elem.type) }}</el-tag>
                <span class="text-xs text-slate-400">分值: {{ elem.exam_config?.score || 5 }}分</span>
              </div>

              <div class="card-actions-mini flex items-center gap-1" @click.stop>
                <el-button link size="small" :disabled="index === 0" @click="moveElem(index, -1)">
                  <ArrowUp :size="13" />
                </el-button>
                <el-button link size="small" :disabled="index === elements.length - 1" @click="moveElem(index, 1)">
                  <ArrowDown :size="13" />
                </el-button>
                <el-button link type="danger" size="small" @click="removeElem(index)">
                  <Trash2 :size="13" />
                </el-button>
              </div>
            </div>

            <!-- 题干快速编辑 -->
            <div class="mt-3">
              <el-input 
                v-model="elem.title" 
                placeholder="请输入题干描述..." 
                size="default"
              />
            </div>

            <!-- 题型专属视觉区 -->
            <div v-if="elem.type === 'Radio' || elem.type === 'Checkbox'" class="mt-3 options-display-area">
              <div v-for="opt in elem.options" :key="opt.value" class="opt-row">
                <span class="opt-mock-check"></span>
                <span class="opt-text">{{ opt.value }}. {{ opt.label }}</span>
                <span v-if="isOptionCorrect(elem, opt.value)" class="opt-correct-tag">✓ 正确答案</span>
              </div>
            </div>

            <div v-else-if="elem.type === 'TrueFalse'" class="mt-3 text-xs text-slate-500">
              设置标准为: <strong>{{ elem.exam_config?.correct_answer === 'true' ? '正确 (True)' : '错误 (False)' }}</strong>
            </div>

            <div v-else-if="elem.type === 'FillBlank'" class="mt-3 text-xs text-slate-400 bg-slate-50 p-2 rounded">
              考生将在此输入填空文本（支持设置标准关键词自动比对）
            </div>

            <div v-else class="mt-3 text-xs text-slate-400 bg-slate-50 p-2 rounded">
              多行大文本输入框，交卷后进入主观题流水阅卷池
            </div>
          </div>
        </div>
      </main>

      <!-- 右侧：属性设置面板 (Inspector) -->
      <aside class="inspector-panel app-card">
        <div class="panel-title flex items-center">
          <Settings :size="16" class="text-slate-600 mr-1.5" /> 属性配置
        </div>

        <!-- 试卷全局设置 -->
        <div v-if="!selectedElem" class="global-settings mt-3">
          <div class="text-xs font-bold text-slate-600 mb-2">试卷全局参数</div>
          <el-form label-position="top" size="small">
            <el-form-item label="建议作答时长 (分钟)">
              <el-input-number v-model="paperForm.suggest_duration" :min="5" :max="240" class="w-full" />
            </el-form-item>
            <el-form-item label="及格分数线 (分)">
              <el-input-number v-model="paperForm.pass_score" :min="1" :max="1000" class="w-full" />
            </el-form-item>
            <el-form-item label="试卷分类">
              <el-input v-model="paperForm.category" placeholder="如：合规、安全、技术研发" />
            </el-form-item>
            <el-form-item label="试卷说明">
              <el-input v-model="paperForm.description" type="textarea" :rows="3" placeholder="考生作答前展示的须知与说明" />
            </el-form-item>
          </el-form>
        </div>

        <!-- 当前选中题目属性配置 -->
        <div v-else class="element-settings mt-3">
          <div class="flex justify-between items-center mb-3">
            <span class="text-xs font-bold text-blue-600">当前正在配置第 {{ getSelectedElemIndex() }} 题</span>
            <el-button link size="small" @click="selectedElem = null">切回试卷全局</el-button>
          </div>

          <el-form label-position="top" size="small">
            <el-form-item label="题目分值 (分)" required>
              <el-input-number v-model="selectedElem.exam_config.score" :min="1" :max="100" class="w-full" />
            </el-form-item>

            <!-- 选项编辑管理 (单选/多选) -->
            <template v-if="selectedElem.type === 'Radio' || selectedElem.type === 'Checkbox'">
              <el-form-item label="选项内容与管理">
                <div class="flex flex-col gap-2 w-full">
                  <div v-for="(opt, idx) in selectedElem.options" :key="opt.value" class="flex gap-2 items-center">
                    <span class="w-6 font-bold text-slate-500 text-center">{{ opt.value }}</span>
                    <el-input v-model="opt.label" :placeholder="`选项 ${opt.value} 描述`" class="flex-1" />
                    <el-button link type="danger" size="small" :disabled="selectedElem.options.length <= 2" @click="removeOption(selectedElem, idx)">
                      <Trash2 :size="12" />
                    </el-button>
                  </div>
                  <el-button size="small" plain type="primary" class="mt-1" @click="addOption(selectedElem)">
                    + 添加选项
                  </el-button>
                </div>
              </el-form-item>

              <el-form-item label="正确答案 (单选)" v-if="selectedElem.type === 'Radio'" required>
                <el-select v-model="selectedElem.exam_config.correct_answer[0]" placeholder="选择正确选项" class="w-full">
                  <el-option v-for="opt in selectedElem.options" :key="opt.value" :label="`${opt.value}. ${opt.label}`" :value="opt.value" />
                </el-select>
              </el-form-item>

              <el-form-item label="正确答案 (多选)" v-else required>
                <el-select v-model="selectedElem.exam_config.correct_answer" multiple placeholder="多选正确答案" class="w-full">
                  <el-option v-for="opt in selectedElem.options" :key="opt.value" :label="`${opt.value}. ${opt.label}`" :value="opt.value" />
                </el-select>
              </el-form-item>
            </template>

            <template v-else-if="selectedElem.type === 'TrueFalse'">
              <el-form-item label="正确答案 (判断)" required>
                <el-radio-group v-model="selectedElem.exam_config.correct_answer[0]">
                  <el-radio label="true">正确</el-radio>
                  <el-radio label="false">错误</el-radio>
                </el-radio-group>
              </el-form-item>
            </template>

            <template v-else-if="selectedElem.type === 'FillBlank'">
              <el-form-item label="标准答案关键词 (支持多个同义词以英文逗号分隔)">
                <el-input 
                  v-model="fillBlankAnswerStr" 
                  placeholder="如：FastAPI, fastapi, 异步框架" 
                  @input="onFillBlankAnswerChange"
                />
              </el-form-item>
            </template>

            <template v-else>
              <el-form-item label="主观题采分点与参考标准 (供阅卷考官参考)">
                <el-input 
                  v-model="selectedElem.exam_config.correct_answer[0]" 
                  type="textarea" 
                  :rows="3" 
                  placeholder="写明回答要点及分值分布" 
                />
              </el-form-item>
            </template>

            <el-form-item label="所属知识点标签">
              <el-input v-model="selectedElem.exam_config.knowledge_tag" placeholder="用于统计员工知识盲区" />
            </el-form-item>

            <el-form-item label="答案官方解析">
              <el-input v-model="selectedElem.exam_config.analysis" type="textarea" :rows="2" placeholder="交卷后向考生展示" />
            </el-form-item>
          </el-form>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { paperApi } from '@/api'
import { ElMessage } from 'element-plus'
import {
  LayoutGrid,
  CircleDot,
  CheckSquare,
  Scale,
  FileEdit,
  FileText,
  Palette,
  ArrowUp,
  ArrowDown,
  Trash2,
  Settings
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const paperId = route.params.id
const saving = ref(false)
const selectedElem = ref(null)
const fillBlankAnswerStr = ref('')

const paperForm = ref({
  title: '新建考核试卷',
  description: '',
  category: '综合测试',
  suggest_duration: 60,
  pass_score: 60
})

const elements = ref([])

const calculatedTotalScore = computed(() => {
  return elements.value.reduce((sum, elem) => sum + (Number(elem.exam_config?.score) || 0), 0)
})

const fetchPaperDetail = async () => {
  if (!paperId) return
  try {
    const res = await paperApi.getPaper(paperId)
    paperForm.value = {
      title: res.title,
      description: res.description || '',
      category: res.category,
      suggest_duration: res.suggest_duration,
      pass_score: res.pass_score
    }
    const page = res.schema_data?.pages?.[0]
    elements.value = page?.elements || []
  } catch (e) {
    ElMessage.error('加载试卷详情失败')
  }
}

const addQuestion = (type) => {
  const newId = `q_${Date.now()}`
  let defaultOptions = []
  let defaultCorrectAns = []

  if (type === 'Radio') {
    defaultOptions = [
      { label: '选项A', value: 'A' },
      { label: '选项B', value: 'B' },
      { label: '选项C', value: 'C' },
      { label: '选项D', value: 'D' }
    ]
    defaultCorrectAns = ['A']
  } else if (type === 'Checkbox') {
    defaultOptions = [
      { label: '选项A', value: 'A' },
      { label: '选项B', value: 'B' },
      { label: '选项C', value: 'C' },
      { label: '选项D', value: 'D' }
    ]
    defaultCorrectAns = ['A', 'B']
  } else if (type === 'TrueFalse') {
    defaultOptions = [
      { label: '正确', value: 'true' },
      { label: '错误', value: 'false' }
    ]
    defaultCorrectAns = ['true']
  } else if (type === 'FillBlank') {
    defaultCorrectAns = ['标准答案']
  } else {
    defaultCorrectAns = ['请根据采分点酌情给分']
  }

  const newElem = {
    id: newId,
    type: type,
    title: `点击输入${getTypeName(type)}题干...`,
    options: defaultOptions,
    required: true,
    exam_config: {
      score: 5,
      correct_answer: defaultCorrectAns,
      analysis: '',
      knowledge_tag: '通用基础',
      difficulty: 'medium'
    }
  }

  elements.value.push(newElem)
  selectElement(newElem)
}

const selectElement = (elem) => {
  selectedElem.value = elem
  if (elem.type === 'FillBlank') {
    fillBlankAnswerStr.value = (elem.exam_config.correct_answer || []).join(', ')
  }
}

const getSelectedElemIndex = () => {
  if (!selectedElem.value) return 1
  return elements.value.findIndex(e => e.id === selectedElem.value.id) + 1
}

const onFillBlankAnswerChange = () => {
  if (selectedElem.value) {
    selectedElem.value.exam_config.correct_answer = fillBlankAnswerStr.value.split(',').map(s => s.trim()).filter(Boolean)
  }
}

const addOption = (elem) => {
  const letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
  const nextVal = letters[elem.options.length] || `Opt${elem.options.length + 1}`
  elem.options.push({ label: `选项${nextVal}`, value: nextVal })
}

const removeOption = (elem, idx) => {
  if (elem.options.length <= 2) {
    ElMessage.warning('单选/多选至少保留两个选项')
    return
  }
  elem.options.splice(idx, 1)
}

const moveElem = (index, delta) => {
  const targetIdx = index + delta
  if (targetIdx < 0 || targetIdx >= elements.value.length) return
  const temp = elements.value[index]
  elements.value[index] = elements.value[targetIdx]
  elements.value[targetIdx] = temp
}

const removeElem = (index) => {
  if (selectedElem.value?.id === elements.value[index].id) {
    selectedElem.value = null
  }
  elements.value.splice(index, 1)
}

const savePaper = async () => {
  if (!paperForm.value.title) {
    ElMessage.warning('请输入试卷标题')
    return
  }
  if (elements.value.length === 0) {
    ElMessage.warning('试卷中至少需要添加一道题目')
    return
  }

  saving.value = true
  const schemaData = {
    pages: [
      {
        id: 'page_1',
        title: paperForm.value.title,
        elements: elements.value
      }
    ]
  }

  const payload = {
    title: paperForm.value.title,
    description: paperForm.value.description,
    category: paperForm.value.category,
    suggest_duration: paperForm.value.suggest_duration,
    total_score: calculatedTotalScore.value,
    pass_score: paperForm.value.pass_score,
    schema_data: schemaData
  }

  try {
    if (paperId) {
      await paperApi.updatePaper(paperId, payload)
      ElMessage.success('试卷更新成功！')
    } else {
      await paperApi.createPaper(payload)
      ElMessage.success('试卷创建成功！')
    }
    router.push('/admin/papers')
  } catch (e) {
    //
  } finally {
    saving.value = false
  }
}

const goBack = () => {
  router.push('/admin/papers')
}

const getTypeName = (type) => {
  const map = {
    Radio: '单选',
    Checkbox: '多选',
    TrueFalse: '判断',
    FillBlank: '填空',
    Textarea: '问答'
  }
  return map[type] || type
}

const getTypeTag = (type) => {
  const map = {
    Radio: 'primary',
    Checkbox: 'success',
    TrueFalse: 'warning',
    FillBlank: 'info',
    Textarea: 'danger'
  }
  return map[type] || 'info'
}

const isOptionCorrect = (elem, optValue) => {
  if (!elem || !elem.exam_config) return false
  const ans = elem.exam_config.correct_answer
  if (Array.isArray(ans)) {
    return ans.includes(optValue)
  }
  return ans === optValue
}

onMounted(() => {
  fetchPaperDetail()
})
</script>

<style scoped>
.paper-editor-layout {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 100px);
}

.editor-header {
  height: 56px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.paper-title-input {
  border: none;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  outline: none;
  width: 60%;
  background: transparent;
}
.paper-title-input:focus {
  border-bottom: 2px solid #3b82f6;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.score-summary {
  font-size: 13px;
  color: #64748b;
  display: flex;
  gap: 10px;
  align-items: center;
}

.editor-workspace {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
}

.toolbox-panel {
  width: 220px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  flex-shrink: 0;
  overflow-y: auto;
}

.panel-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}
.panel-subtitle {
  font-size: 11px;
  color: #94a3b8;
  margin-bottom: 14px;
}

.tools-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tool-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: left;
}
.tool-btn:hover {
  background: #eff6ff;
  border-color: #93c5fd;
  transform: translateX(2px);
}

.tool-icon {
  font-size: 18px;
}
.tool-info .name {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  color: #1e293b;
}
.tool-info .desc {
  display: block;
  font-size: 10px;
  color: #94a3b8;
}

.canvas-area {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.elements-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.canvas-card {
  background: white;
  padding: 18px 20px;
  border-radius: 12px;
  border: 1.5px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.15s ease;
}
.canvas-card:hover {
  border-color: #cbd5e1;
}
.canvas-card.is-selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.card-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.elem-index {
  background: #0f172a;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}

.inspector-panel {
  width: 290px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  flex-shrink: 0;
  overflow-y: auto;
}
</style>
