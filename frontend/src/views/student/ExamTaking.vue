<template>
  <div class="exam-taking-page exam-taking-body" :class="{ 'blur-guard': screenSwitchWarning }">
    <!-- 顶部状态导航栏 -->
    <header class="exam-top-bar glass-panel">
      <div class="top-left">
        <div class="paper-title-tag">
          <span class="badge">正式考核</span>
          <h2 class="title">{{ examInfo?.title || '在线考试' }}</h2>
        </div>
      </div>

      <div class="top-center">
        <!-- 倒计时 -->
        <div class="timer-box" :class="{ 'timer-danger': remainingSeconds < 300 }">
          <svg class="timer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span class="timer-text">{{ formatTime(remainingSeconds) }}</span>
        </div>

        <!-- 切屏警告指示（仅在开启了防切屏且 max_screen_switch > 0 时显示） -->
        <div 
          v-if="examInfo?.max_screen_switch && examInfo.max_screen_switch > 0"
          class="switch-guard-tag" 
          :class="screenSwitchCount > 0 ? 'guard-alert' : ''"
        >
          <ShieldAlert :size="15" class="guard-icon" />
          <span class="guard-text">切屏监控: {{ screenSwitchCount }} / {{ examInfo.max_screen_switch }} 次</span>
        </div>
      </div>

      <div class="top-right">
        <div class="progress-info">
          <span class="progress-text">完成度: <strong>{{ answeredCount }}</strong> / {{ totalQuestions }}</span>
          <el-progress 
            :percentage="progressPercentage" 
            :show-text="false" 
            :stroke-width="6"
            class="progress-bar"
          />
        </div>
        <el-button type="primary" class="submit-btn" :loading="submitting" @click="confirmSubmit">
          交卷
        </el-button>
      </div>
    </header>

    <!-- 主体作答区 -->
    <div class="exam-main-content">
      <!-- 中间题目展示区 -->
      <div class="questions-scroll-area">
        <div 
          v-for="(elem, index) in questions" 
          :key="elem.id" 
          :id="`question-${elem.id}`"
          class="question-card app-card"
          :class="{ 'card-active': currentActiveId === elem.id }"
        >
          <div class="q-header">
            <div class="q-left-info">
              <span class="q-index-badge">{{ index + 1 }}</span>
              <el-tag size="small" :type="getTypeTag(elem.type)" effect="light">
                {{ getTypeName(elem.type) }}
              </el-tag>
              <span class="q-score">({{ elem.exam_config?.score || 5 }}分)</span>
            </div>
            <span class="q-tag">{{ elem.exam_config?.knowledge_tag || '通用知识' }}</span>
          </div>

          <div class="q-title">
            {{ elem.title }}
          </div>

          <!-- 单选题 (Radio) -->
          <div v-if="elem.type.toLowerCase() === 'radio'" class="options-group">
            <label 
              v-for="opt in elem.options" 
              :key="opt.value" 
              class="option-item"
              :class="{ 'selected': answers[elem.id] === opt.value }"
            >
              <input 
                type="radio" 
                :name="elem.id" 
                :value="opt.value" 
                v-model="answers[elem.id]"
                @change="onAnswerChange(elem.id)"
              />
              <span class="opt-key">{{ opt.value }}</span>
              <span class="opt-label">{{ opt.label }}</span>
            </label>
          </div>

          <!-- 多选题 (Checkbox) -->
          <div v-else-if="elem.type.toLowerCase() === 'checkbox'" class="options-group">
            <label 
              v-for="opt in elem.options" 
              :key="opt.value" 
              class="option-item"
              :class="{ 'selected': (answers[elem.id] || []).includes(opt.value) }"
            >
              <input 
                type="checkbox" 
                :value="opt.value" 
                :checked="(answers[elem.id] || []).includes(opt.value)"
                @change="toggleCheckbox(elem.id, opt.value)"
              />
              <span class="opt-key">{{ opt.value }}</span>
              <span class="opt-label">{{ opt.label }}</span>
            </label>
          </div>

          <!-- 判断题 (TrueFalse) -->
          <div v-else-if="elem.type.toLowerCase() === 'truefalse'" class="tf-group">
            <button 
              type="button"
              class="tf-btn true-btn"
              :class="{ 'active': answers[elem.id] === 'true' }"
              @click="setTfAnswer(elem.id, 'true')"
            >
              <Check :size="17" class="tf-icon" />
              <span>正确 (True)</span>
            </button>
            <button 
              type="button"
              class="tf-btn false-btn"
              :class="{ 'active': answers[elem.id] === 'false' }"
              @click="setTfAnswer(elem.id, 'false')"
            >
              <X :size="17" class="tf-icon" />
              <span>错误 (False)</span>
            </button>
          </div>

          <!-- 填空题 (FillBlank) -->
          <div v-else-if="elem.type.toLowerCase() === 'fillblank'" class="fill-blank-box">
            <el-input 
              v-model="answers[elem.id]" 
              placeholder="请在此输入您的答案..." 
              size="large"
              clearable
              @input="onAnswerChange(elem.id)"
            />
          </div>

          <!-- 问答/简答题 (Textarea) -->
          <div v-else class="essay-box">
            <el-input 
              v-model="answers[elem.id]" 
              type="textarea" 
              :rows="4" 
              placeholder="请输入您的详细论述与回答..." 
              @input="onAnswerChange(elem.id)"
            />
          </div>
        </div>
      </div>

      <!-- 右侧答题卡悬浮导航 -->
      <aside class="answer-sheet-panel app-card">
        <div class="sheet-header">
          <h4>答题卡</h4>
          <span class="auto-save-text">
            <span class="save-dot"></span> 实时已暂存
          </span>
        </div>

        <div class="sheet-legend">
          <div class="legend-item"><span class="legend-box answered"></span> 已答</div>
          <div class="legend-item"><span class="legend-box unanswer"></span> 未答</div>
        </div>

        <div class="sheet-grid">
          <button 
            v-for="(elem, idx) in questions" 
            :key="elem.id"
            class="sheet-btn"
            :class="{ 'is-answered': isQuestionAnswered(elem.id) }"
            @click="scrollToQuestion(elem.id)"
          >
            {{ idx + 1 }}
          </button>
        </div>
      </aside>
    </div>

    <!-- 切屏作弊警告弹窗 -->
    <el-dialog
      v-model="screenSwitchWarning"
      title="考场防作弊监控警示"
      width="420px"
      :show-close="false"
      :close-on-click-modal="false"
      center
    >
      <div class="text-center py-2">
        <p class="text-red-500 font-bold text-base mb-2">检测到您离开了考试页面！</p>
        <p class="text-slate-600 text-sm">
          切屏次数：<strong>{{ screenSwitchCount }}</strong> / {{ examInfo?.max_screen_switch }} 次
        </p>
        <p class="text-xs text-slate-400 mt-2">若切屏次数超过上限，系统将自动锁定考卷并强制提交。</p>
      </div>
      <template #footer>
        <el-button type="primary" @click="closeWarningDialog">我知道了，继续答题</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { examApi } from '@/api'
import { ElMessageBox, ElMessage } from 'element-plus'
import confetti from 'canvas-confetti'
import { Check, X, ShieldAlert } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const examId = route.params.id
const recordId = ref(null)
const examInfo = ref(null)
const questions = ref([])
const answers = ref({})
const screenSwitchCount = ref(0)
const remainingSeconds = ref(3600)
const screenSwitchWarning = ref(false)
const submitting = ref(false)
const currentActiveId = ref('')

let timerInterval = null
let autoSaveInterval = null

const totalQuestions = computed(() => questions.value.length)

const isQuestionAnswered = (qId) => {
  const val = answers.value[qId]
  if (val === undefined || val === null || val === '') return false
  if (Array.isArray(val) && val.length === 0) return false
  return true
}

const answeredCount = computed(() => {
  return questions.value.filter(q => isQuestionAnswered(q.id)).length
})

const progressPercentage = computed(() => {
  if (totalQuestions.value === 0) return 0
  return Math.round((answeredCount.value / totalQuestions.value) * 100)
})

const fetchExamData = async () => {
  try {
    const res = await examApi.startOrResumeExam(examId)
    recordId.value = res.record_id
    examInfo.value = res.exam_task
    screenSwitchCount.value = res.screen_switch_count || 0

    // 解析题目
    const extracted = []
    for (const page of res.schema?.pages || []) {
      for (const elem of page.elements || []) {
        extracted.push(elem)
      }
    }
    questions.value = extracted

    // 载入草稿答案
    answers.value = res.draft_answers || {}

    // 计算倒计时
    const durationSec = (res.exam_task.duration_minutes || 60) * 60
    const elapsed = res.duration_seconds || 0
    remainingSeconds.value = Math.max(0, durationSec - elapsed)

    startTimers()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '进入考试失败')
    router.replace('/student/exams')
  }
}

const startTimers = () => {
  // 倒计时
  timerInterval = setInterval(() => {
    if (remainingSeconds.value > 0) {
      remainingSeconds.value--
    } else {
      clearInterval(timerInterval)
      ElMessage.warning('考试时间已截止，正在自动为您交卷...')
      submitExamAction(true)
    }
  }, 1000)

  // 自动暂存心跳（每 15 秒）
  autoSaveInterval = setInterval(() => {
    saveDraft()
  }, 15000)
}

const saveDraft = async () => {
  if (!recordId.value) return
  try {
    await examApi.saveDraft(recordId.value, {
      answers: answers.value,
      screen_switch_count: screenSwitchCount.value,
      duration_seconds: (examInfo.value.duration_minutes * 60) - remainingSeconds.value
    })
  } catch (e) {
    console.error('Draft save failed:', e)
  }
}

// 答案交互
const onAnswerChange = (qId) => {
  currentActiveId.value = qId
  localStorage.setItem(`exam_draft_${recordId.value}`, JSON.stringify(answers.value))
}

const toggleCheckbox = (qId, val) => {
  let list = answers.value[qId] || []
  if (list.includes(val)) {
    list = list.filter(x => x !== val)
  } else {
    list = [...list, val]
  }
  answers.value[qId] = list
  onAnswerChange(qId)
}

const setTfAnswer = (qId, val) => {
  answers.value[qId] = val
  onAnswerChange(qId)
}

const scrollToQuestion = (qId) => {
  currentActiveId.value = qId
  const el = document.getElementById(`question-${qId}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }
}

// 防切屏作弊监控
const handleVisibilityChange = () => {
  const maxLimit = Number(examInfo.value?.max_screen_switch) || 0
  // 当最大切屏次数设为 0 时表示“不限制切屏”，不弹警告也不强制收卷
  if (maxLimit <= 0) {
    return
  }
  if (document.hidden) {
    screenSwitchCount.value++
    saveDraft()
    if (screenSwitchCount.value >= maxLimit) {
      ElMessageBox.alert(
        `您切屏已达 ${screenSwitchCount.value} 次（考场允许最大切屏 ${maxLimit} 次），已触发强制交卷！`,
        '切屏违规交卷',
        { confirmButtonText: '确定', callback: () => submitExamAction(true) }
      )
    } else {
      screenSwitchWarning.value = true
    }
  }
}

const closeWarningDialog = () => {
  screenSwitchWarning.value = false
}

// 交卷确认
const confirmSubmit = () => {
  const unanswered = totalQuestions.value - answeredCount.value
  let msg = '确定要提交试卷吗？交卷后将立即出分。'
  if (unanswered > 0) {
    msg = `您还有 ${unanswered} 道题尚未作答，确定要现在提交试卷吗？`
  }

  ElMessageBox.confirm(msg, '确认交卷', {
    confirmButtonText: '确定交卷',
    cancelButtonText: '继续检查',
    type: unanswered > 0 ? 'warning' : 'info'
  }).then(() => {
    submitExamAction(false)
  })
}

const submitExamAction = async (isForce = false) => {
  if (submitting.value) return
  submitting.value = true
  try {
    const res = await examApi.submitExam(recordId.value, {
      answers: answers.value,
      screen_switch_count: screenSwitchCount.value,
      duration_seconds: (examInfo.value?.duration_minutes * 60) - remainingSeconds.value
    })

    // 庆祝彩屑特效
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    })

    ElMessage.success(res.message || '交卷成功！')
    router.replace(`/exam/result/${recordId.value}`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '交卷失败')
  } finally {
    submitting.value = false
  }
}

const formatTime = (secs) => {
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const getTypeName = (type) => {
  const map = {
    radio: '单选题',
    checkbox: '多选题',
    truefalse: '判断题',
    fillblank: '填空题',
    textarea: '简答/问答题'
  }
  return map[type.toLowerCase()] || '客观题'
}

const getTypeTag = (type) => {
  const map = {
    radio: 'primary',
    checkbox: 'success',
    truefalse: 'warning',
    fillblank: 'info',
    textarea: 'danger'
  }
  return map[type.toLowerCase()] || 'info'
}

onMounted(() => {
  fetchExamData()
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  clearInterval(timerInterval)
  clearInterval(autoSaveInterval)
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
.exam-taking-page {
  min-height: 100vh;
  background-color: #f1f5f9;
  display: flex;
  flex-direction: column;
}

.exam-top-bar {
  height: 68px;
  padding: 0 32px;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 30;
}

.paper-title-tag {
  display: flex;
  align-items: center;
  gap: 10px;
}
.paper-title-tag .badge {
  background: #eff6ff;
  color: #2563eb;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid #bfdbfe;
}
.paper-title-tag .title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.top-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.timer-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 6px 16px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
}
.timer-icon {
  width: 18px;
  height: 18px;
  color: #3b82f6;
}
.timer-danger {
  background: #fef2f2;
  border-color: #fecaca;
  color: #dc2626;
  animation: pulse 1s infinite;
}
.timer-danger .timer-icon {
  color: #dc2626;
}

.switch-guard-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  background: #f8fafc;
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
  flex-shrink: 0;
}
.switch-guard-tag .guard-icon {
  width: 15px;
  height: 15px;
  flex-shrink: 0;
}
.guard-alert {
  background: #fffbeb;
  border-color: #fde68a;
  color: #d97706;
  font-weight: 600;
}

.top-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.progress-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 120px;
}
.progress-text {
  font-size: 11px;
  color: #64748b;
}
.submit-btn {
  font-weight: 600;
  padding: 0 24px;
  border-radius: 9px;
}

.exam-main-content {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 24px auto;
  padding: 0 20px;
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.questions-scroll-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.question-card {
  background: white;
  padding: 28px;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  transition: border-color 0.2s ease;
}
.card-active {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.q-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.q-left-info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.q-index-badge {
  background: #0f172a;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}
.q-score {
  font-size: 12px;
  color: #64748b;
  font-weight: 600;
}
.q-tag {
  font-size: 11px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 3px 8px;
  border-radius: 6px;
}

.q-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.6;
  margin-bottom: 20px;
}

.options-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  border: 1.5px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.option-item:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}
.option-item.selected {
  border-color: #3b82f6;
  background: #eff6ff;
}
.opt-key {
  width: 26px;
  height: 26px;
  border-radius: 6px;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #475569;
}
.option-item.selected .opt-key {
  background: #3b82f6;
  color: white;
}
.opt-label {
  font-size: 14.5px;
  color: #334155;
}

.tf-group {
  display: flex;
  gap: 14px;
  max-width: 440px;
}
.tf-btn {
  flex: 1;
  height: 44px;
  padding: 0 18px;
  border-radius: 9px;
  border: 1.5px solid #e2e8f0;
  background: white;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  transition: all 0.15s ease;
}
.tf-btn .tf-icon {
  width: 17px;
  height: 17px;
  flex-shrink: 0;
}
.tf-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}
.true-btn.active {
  border-color: #10b981;
  background: #ecfdf5;
  color: #059669;
  box-shadow: 0 1px 3px rgba(16, 185, 129, 0.15);
}
.false-btn.active {
  border-color: #ef4444;
  background: #fef2f2;
  color: #dc2626;
  box-shadow: 0 1px 3px rgba(239, 68, 68, 0.15);
}

.answer-sheet-panel {
  width: 280px;
  position: sticky;
  top: 92px;
  background: white;
  padding: 20px;
  border-radius: 14px;
}
.sheet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.sheet-header h4 {
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}
.auto-save-text {
  font-size: 11px;
  color: #10b981;
  display: flex;
  align-items: center;
  gap: 4px;
}
.save-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
}

.sheet-legend {
  display: flex;
  gap: 14px;
  margin-bottom: 16px;
  font-size: 11.5px;
  color: #64748b;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.legend-box {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}
.legend-box.answered {
  background: #3b82f6;
}
.legend-box.unanswer {
  background: #f1f5f9;
  border: 1px solid #cbd5e1;
}

.sheet-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 8px;
}
.sheet-btn {
  aspect-ratio: 1;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #64748b;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.sheet-btn:hover {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #2563eb;
}
.sheet-btn.is-answered {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
}
</style>
