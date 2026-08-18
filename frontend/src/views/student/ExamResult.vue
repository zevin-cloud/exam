<template>
  <div class="result-container">
    <div v-if="loading" class="text-center py-20">
      <el-icon class="is-loading" :size="32" color="#3b82f6"><Loading /></el-icon>
      <p class="text-slate-400 mt-2 text-sm">正在加载答卷与解析报告...</p>
    </div>

    <template v-else-if="resultData">
      <!-- 成绩概览大看板 -->
      <div class="score-banner app-card">
        <div class="banner-left">
          <div class="badge-status-row">
            <span class="exam-name-tag">{{ resultData.record.exam_title }}</span>
            <el-tag :type="resultData.record.is_passed ? 'success' : 'danger'" size="large" effect="dark" class="pass-tag">
              <span class="flex items-center gap-1.5">
                <CheckCircle2 v-if="resultData.record.is_passed" :size="15" />
                <AlertCircle v-else :size="15" />
                {{ resultData.record.is_passed ? '考核及格' : '暂未及格' }}
              </span>
            </el-tag>
          </div>
          <h1 class="score-display">
            {{ resultData.record.total_score }} <span class="unit">分</span>
          </h1>
          <p class="score-sub">
            试卷总分 {{ resultData.record.total_paper_score }} 分 | 及格线 {{ resultData.record.pass_score }} 分
            (客观题: {{ resultData.record.objective_score }}分 / 主观题: {{ resultData.record.subjective_score }}分)
          </p>
        </div>

        <div class="banner-right">
          <div class="metric-group">
            <div class="metric-item">
              <span class="m-label">作答用时</span>
              <span class="m-val">{{ formatDuration(resultData.record.duration_seconds) }}</span>
            </div>
            <div class="metric-item">
              <span class="m-label">切屏次数</span>
              <span class="m-val" :class="resultData.record.screen_switch_count > 0 ? 'text-amber-600' : ''">
                {{ resultData.record.screen_switch_count }} 次
              </span>
            </div>
            <div class="metric-item">
              <span class="m-label">交卷状态</span>
              <span class="m-val text-blue-600 font-semibold">
                {{ resultData.record.status === 'GRADED' ? '已完成批阅' : '主观题阅卷中' }}
              </span>
            </div>
          </div>
          <el-button type="primary" plain class="mt-4 w-full" @click="backToList">
            返回考务中心
          </el-button>
        </div>
      </div>

      <!-- 答题解析列表（当开启允许查看时） -->
      <div v-if="resultData.record.allow_view_details !== false" class="analysis-section">
        <div class="section-header flex justify-between items-center mb-4">
          <h3 class="flex items-center gap-2 text-base font-bold text-slate-800">
            <FileText :size="18" class="text-blue-600" />
            答题明细与试题解析
          </h3>
          <div class="filter-pills flex items-center gap-2">
            <span class="pill correct">正确: {{ correctCount }} 题</span>
            <span class="pill wrong">错误/待阅: {{ wrongCount }} 题</span>
          </div>
        </div>

        <div class="detail-list flex flex-col gap-4">
          <div 
            v-for="(item, idx) in resultData.details" 
            :key="item.id || idx"
            class="detail-card app-card"
            :class="getCardBorderClass(item)"
          >
            <!-- 题目顶部头部 -->
            <div class="detail-card-header flex justify-between items-center pb-3 border-b border-slate-100 mb-3">
              <div class="q-seq-type flex items-center gap-2">
                <span class="q-index font-bold text-slate-700">第 {{ idx + 1 }} 题</span>
                <el-tag size="small" :type="getTypeTag(item.question_type)">
                  {{ getTypeName(item.question_type) }}
                </el-tag>
                <span class="text-xs text-slate-400">满分: {{ item.max_score }}分</span>
              </div>

              <div class="score-status">
                <span 
                  v-if="item.is_correct === true" 
                  class="status-pill status-correct"
                >
                  ✓ 得满分 ({{ item.actual_score }}分)
                </span>
                <span 
                  v-else-if="item.is_correct === false && item.actual_score === 0" 
                  class="status-pill status-wrong"
                >
                  ✗ 错误 (0分)
                </span>
                <span 
                  v-else-if="item.actual_score > 0" 
                  class="status-pill status-partial"
                >
                  部分得分 ({{ item.actual_score }} / {{ item.max_score }}分)
                </span>
                <span v-else class="status-pill status-pending">
                  待考官批阅
                </span>
              </div>
            </div>

            <!-- 题目内容 -->
            <div class="question-body">
              <div class="q-title text-sm font-bold text-slate-800 mb-3 leading-relaxed">
                {{ item.question_title }}
              </div>

              <!-- 选择题选项渲染与对比 -->
              <div v-if="item.options && item.options.length" class="options-list flex flex-col gap-2 mb-4">
                <div 
                  v-for="opt in item.options" 
                  :key="opt.value"
                  class="option-item flex items-center gap-2 p-2.5 rounded-lg border text-xs"
                  :class="getOptionClass(opt.value, item)"
                >
                  <span class="opt-key font-bold w-5 text-center">{{ opt.value }}.</span>
                  <span class="opt-label flex-1">{{ opt.label }}</span>
                  <span v-if="isOptionInAnswer(opt.value, item.correct_answer)" class="text-emerald-600 font-bold ml-2">
                    [正确答案]
                  </span>
                  <span v-if="isOptionInAnswer(opt.value, item.user_answer)" class="text-blue-600 font-semibold ml-2">
                    [您的选择]
                  </span>
                </div>
              </div>

              <!-- 答案对比与展示 -->
              <div class="answer-comparison bg-slate-50 p-3 rounded-lg flex flex-col gap-1.5 text-xs mb-3">
                <div class="ans-row flex items-baseline gap-2">
                  <span class="ans-label text-slate-500 font-medium">您的作答：</span>
                  <span class="ans-text font-bold font-mono" :class="item.is_correct ? 'text-emerald-600' : 'text-rose-600'">
                    {{ formatAnswerText(item.user_answer) }}
                  </span>
                </div>
                <div class="ans-row flex items-baseline gap-2">
                  <span class="ans-label text-slate-500 font-medium">参考标准答案：</span>
                  <span class="ans-text text-emerald-700 font-bold font-mono">
                    {{ formatAnswerText(item.correct_answer) }}
                  </span>
                </div>
              </div>

              <!-- 官方解析 -->
              <div v-if="item.analysis" class="analysis-box p-3 bg-blue-50/40 rounded-lg border border-blue-100 text-xs mb-2">
                <div class="box-title flex items-center gap-1.5 font-bold text-blue-700 mb-1">
                  <HelpCircle :size="14" class="text-blue-600" /> 试题解析：
                </div>
                <div class="box-content text-slate-700 leading-relaxed">{{ item.analysis }}</div>
              </div>

              <!-- 考官阅卷评语 (针对主观题) -->
              <div v-if="item.teacher_comment" class="teacher-comment-box p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs mt-2">
                <span class="comment-label flex items-center gap-1 font-bold text-amber-800 mb-1">
                  <MessageSquare :size="14" /> 考官阅卷评语：
                </span>
                <span class="ans-text text-amber-900 leading-relaxed">
                  {{ item.teacher_comment }}
                </span>
              </div>
            </div>

            <!-- 底部标签 -->
            <div class="detail-footer pt-3 mt-3 border-t border-slate-100 flex justify-between items-center text-xs text-slate-400">
              <span class="knowledge-pill flex items-center gap-1">
                <Tag :size="12" class="text-slate-400" /> 知识点: {{ item.knowledge_tag || '通用素养' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 保密模式（管理员关闭了详情查看） -->
      <div v-else class="security-mode-card app-card text-center py-12 px-6">
        <div class="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-500">
          <svg class="w-7 h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>
        <h3 class="text-base font-bold text-slate-700 mb-1">本次考务开启了安全保密模式</h3>
        <p class="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
          根据本次考核发布规则，考务管理员未开放试题解析与答题明细查看权限。您的作答记录与成绩已安全归档入库。
        </p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { examApi } from '@/api'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  CheckCircle2,
  AlertCircle,
  FileText,
  HelpCircle,
  MessageSquare,
  Tag
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const recordId = route.params.recordId
const loading = ref(true)
const resultData = ref(null)

const fetchResult = async () => {
  loading.value = true
  try {
    const res = await examApi.getExamResult(recordId)
    resultData.value = res
  } catch (e) {
    ElMessage.error('获取答卷结果失败')
  } finally {
    loading.value = false
  }
}

const correctCount = computed(() => {
  if (!resultData.value?.details) return 0
  return resultData.value.details.filter(d => d.is_correct === true).length
})

const wrongCount = computed(() => {
  if (!resultData.value?.details) return 0
  return resultData.value.details.filter(d => d.is_correct !== true).length
})

const formatDuration = (secs) => {
  if (!secs) return '0秒'
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

const isOptionInAnswer = (optValue, answerObj) => {
  if (answerObj === undefined || answerObj === null) return false
  if (Array.isArray(answerObj)) {
    return answerObj.includes(optValue)
  }
  return answerObj === optValue
}

const getOptionClass = (optValue, item) => {
  const isCorrect = isOptionInAnswer(optValue, item.correct_answer)
  const isUserSelected = isOptionInAnswer(optValue, item.user_answer)

  if (isCorrect && isUserSelected) {
    return 'bg-emerald-50 border-emerald-300 text-emerald-800'
  }
  if (isCorrect) {
    return 'bg-emerald-50/50 border-emerald-200 text-emerald-700'
  }
  if (isUserSelected && !isCorrect) {
    return 'bg-rose-50 border-rose-200 text-rose-700'
  }
  return 'bg-white border-slate-200 text-slate-600'
}

const formatAnswerText = (ans) => {
  if (ans === undefined || ans === null || ans === '' || (Array.isArray(ans) && ans.length === 0)) {
    return '(考生未作答)'
  }
  if (Array.isArray(ans)) return ans.join(', ')
  if (typeof ans === 'boolean') return ans ? '正确 (True)' : '错误 (False)'
  if (ans === 'true') return '正确 (True)'
  if (ans === 'false') return '错误 (False)'
  return String(ans)
}

const getCardBorderClass = (item) => {
  if (item.is_correct === true) return 'border-l-4 border-l-emerald-500'
  if (item.is_graded === false) return 'border-l-4 border-l-amber-400'
  return 'border-l-4 border-l-rose-500'
}

const getTypeName = (type) => {
  if (!type) return '题目'
  const map = {
    radio: '单选题',
    checkbox: '多选题',
    truefalse: '判断题',
    fillblank: '填空题',
    textarea: '简答/问答题',
    essay: '简答/问答题'
  }
  return map[type.toLowerCase()] || type
}

const getTypeTag = (type) => {
  if (!type) return 'info'
  const map = {
    radio: 'primary',
    checkbox: 'success',
    truefalse: 'warning',
    fillblank: 'info',
    textarea: 'danger',
    essay: 'danger'
  }
  return map[type.toLowerCase()] || 'info'
}

const backToList = () => {
  router.push('/student/exams')
}

onMounted(() => {
  fetchResult()
})
</script>

<style scoped>
.result-container {
  max-width: 960px;
  margin: 0 auto;
}

.score-banner {
  background: white;
  padding: 28px 32px;
  border-radius: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 24px;
}

.badge-status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.exam-name-tag {
  font-size: 13px;
  color: #64748b;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}
.pass-tag {
  font-weight: 700;
  border-radius: 6px;
}

.score-display {
  font-size: 44px;
  font-weight: 900;
  color: #0f172a;
  line-height: 1;
  margin-bottom: 8px;
}
.unit {
  font-size: 20px;
  font-weight: 500;
  color: #64748b;
}
.score-sub {
  font-size: 12.5px;
  color: #64748b;
}

.banner-right {
  min-width: 240px;
}
.metric-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #f8fafc;
  padding: 12px 16px;
  border-radius: 10px;
}
.metric-item {
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
}
.m-label { color: #64748b; }
.m-val { font-weight: 600; color: #1e293b; }

.filter-pills {
  display: flex;
  gap: 8px;
}
.pill {
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}
.pill.correct { background: #ecfdf5; color: #059669; }
.pill.wrong { background: #fef2f2; color: #e11d48; }

.detail-card {
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
}

.status-pill {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
}
.status-correct { background: #ecfdf5; color: #059669; }
.status-wrong { background: #fef2f2; color: #e11d48; }
.status-partial { background: #f0fdf4; color: #16a34a; }
.status-pending { background: #fffbeb; color: #d97706; }
</style>
