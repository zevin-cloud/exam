<template>
  <div class="result-page">
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="32" color="#2b6f9f"><Loading /></el-icon>
      <p>正在调取归档答卷...</p>
    </div>

    <template v-else-if="resultData">
      <header class="document-toolbar">
        <button type="button" class="back-button" @click="backToList">
          <ArrowLeft :size="16" /> {{ backLabel }}
        </button>
        <div class="archive-mark">
          <span>答卷详情</span>
          <strong>#{{ resultData.record.id }}</strong>
        </div>
      </header>

      <section class="paper-masthead">
        <div class="masthead-copy">
          <div class="paper-eyebrow">
            <span>{{ resultData.record.exam_title }}</span>
            <i></i>
            <span>第 {{ resultData.record.attempt_no }} 次有效作答</span>
          </div>
          <h1>{{ resultData.record.paper_title }}</h1>
          <div class="candidate-line">
            <div>
              <span>考生</span>
              <strong>{{ resultData.record.student_name }}</strong>
              <small v-if="resultData.record.student_username">{{ resultData.record.student_username }}</small>
            </div>
            <div>
              <span>交卷时间</span>
              <strong>{{ formatDate(resultData.record.submit_time) }}</strong>
            </div>
            <div>
              <span>卷面状态</span>
              <strong :class="statusTone">{{ recordStatusText }}</strong>
            </div>
          </div>
        </div>

        <div class="score-stamp" :class="statusTone">
          <span>{{ resultData.record.status === 'GRADED' ? '最终成绩' : '客观题暂计' }}</span>
          <strong>{{ resultData.record.status === 'GRADED' ? resultData.record.total_score : resultData.record.objective_score }}</strong>
          <small>/ {{ resultData.record.total_paper_score }} 分</small>
          <em v-if="resultData.record.status === 'GRADED'">{{ resultData.record.is_passed ? '考核通过' : '未达标' }}</em>
          <em v-else>等待主观题评分</em>
        </div>
      </section>

      <div v-if="resultData.record.allow_view_details !== false" class="paper-workspace">
        <main class="paper-stream">
          <div class="stream-toolbar">
            <div>
              <h2>作答卷面</h2>
              <p>共 {{ questionRows.length }} 题，当前显示 {{ filteredDetails.length }} 题</p>
            </div>
            <div class="filter-tabs" aria-label="答卷筛选">
              <button
                v-for="option in filterOptions"
                :key="option.value"
                type="button"
                :class="{ active: activeFilter === option.value }"
                @click="activeFilter = option.value"
              >
                {{ option.label }} <span>{{ option.count }}</span>
              </button>
            </div>
          </div>

          <div v-if="!filteredDetails.length" class="empty-filter">
            当前筛选条件下没有题目
          </div>

          <article
            v-for="row in filteredDetails"
            :id="`question-${row.item.id}`"
            :key="row.item.id"
            class="question-sheet"
            :class="`state-${getQuestionState(row.item)}`"
          >
            <header class="question-heading">
              <div class="question-number">
                <span>{{ String(row.number).padStart(2, '0') }}</span>
                <div>
                  <strong>第 {{ row.number }} 题</strong>
                  <small>{{ getTypeName(row.item.question_type) }} · {{ row.item.max_score }} 分</small>
                </div>
              </div>
              <span class="question-result" :class="`result-${getQuestionState(row.item)}`">
                {{ getQuestionStatusLabel(row.item) }}
              </span>
            </header>

            <div class="question-content">
              <h3>{{ row.item.question_title }}</h3>

              <div v-if="row.item.options?.length" class="option-list">
                <div
                  v-for="option in row.item.options"
                  :key="option.value"
                  class="option-row"
                  :class="getOptionClass(option.value, row.item)"
                >
                  <span class="option-key">{{ option.value }}</span>
                  <span class="option-label">{{ option.label }}</span>
                  <span v-if="isOptionInAnswer(option.value, row.item.user_answer)" class="choice-mark user-choice">考生选择</span>
                  <span v-if="isOptionInAnswer(option.value, row.item.correct_answer)" class="choice-mark correct-choice">正确答案</span>
                </div>
              </div>

              <section v-if="isSubjective(row.item.question_type)" class="subjective-response">
                <div class="section-caption">考生作答</div>
                <div class="answer-paper">
                  <MarkdownAnswer :answer="row.item.user_answer" />
                </div>
                <div class="reference-line">
                  <span>参考答案</span>
                  <p>{{ formatAnswerText(row.item.correct_answer) }}</p>
                </div>
              </section>

              <section v-else class="objective-comparison">
                <div>
                  <span>考生作答</span>
                  <strong :class="getQuestionState(row.item) === 'full' ? 'answer-correct' : 'answer-wrong'">
                    {{ formatAnswerText(row.item.user_answer) }}
                  </strong>
                </div>
                <div>
                  <span>标准答案</span>
                  <strong class="answer-correct">{{ formatAnswerText(row.item.correct_answer) }}</strong>
                </div>
              </section>

              <section v-if="row.item.analysis" class="explanation-box">
                <div class="section-caption"><HelpCircle :size="14" /> 试题解析</div>
                <p>{{ row.item.analysis }}</p>
              </section>

              <section v-if="row.item.teacher_comment" class="teacher-note">
                <div class="section-caption"><MessageSquare :size="14" /> 阅卷评语</div>
                <p>{{ row.item.teacher_comment }}</p>
              </section>
            </div>

            <footer class="question-footer">
              <span><Tag :size="12" /> {{ row.item.knowledge_tag || '通用素养' }}</span>
              <span v-if="row.item.is_graded">本题得分 <strong>{{ row.item.actual_score }}</strong> / {{ row.item.max_score }}</span>
              <span v-else>本题尚未完成评分</span>
            </footer>
          </article>
        </main>

        <aside class="paper-sidebar">
          <section class="sidebar-card score-receipt">
            <div class="sidebar-title">
              <ClipboardCheck :size="17" /> 成绩小结
            </div>
            <div class="score-breakdown">
              <div><span>客观题</span><strong>{{ resultData.record.objective_score }} 分</strong></div>
              <div><span>主观题</span><strong>{{ resultData.record.subjective_score }} 分</strong></div>
              <div class="receipt-total"><span>卷面总分</span><strong>{{ resultData.record.total_score }} 分</strong></div>
            </div>
            <div class="exam-metrics">
              <span><Clock3 :size="13" /> {{ formatDuration(resultData.record.duration_seconds) }}</span>
              <span :class="{ warning: resultData.record.screen_switch_count > 0 }">
                <MonitorUp :size="13" /> 切屏 {{ resultData.record.screen_switch_count }} 次
              </span>
            </div>
          </section>

          <section class="sidebar-card answer-map">
            <div class="sidebar-title">
              <ListFilter :size="17" /> 答题卡
            </div>
            <div class="question-grid">
              <button
                v-for="row in questionRows"
                :key="row.item.id"
                type="button"
                :class="`map-${getQuestionState(row.item)}`"
                :title="`第 ${row.number} 题：${getQuestionStatusLabel(row.item)}`"
                @click="jumpToQuestion(row)"
              >
                {{ row.number }}
              </button>
            </div>
            <div class="map-legend">
              <span><i class="legend-full"></i>满分</span>
              <span><i class="legend-partial"></i>部分得分</span>
              <span><i class="legend-wrong"></i>错误</span>
              <span><i class="legend-pending"></i>待阅</span>
            </div>
          </section>
        </aside>
      </div>

      <div v-else class="security-card">
        <div class="security-icon">保密</div>
        <h3>本次考务未开放答题明细</h3>
        <p>您的成绩与答卷已归档。试题、答案和解析将在管理员开放后显示。</p>
        <el-button type="primary" plain @click="backToList">{{ backLabel }}</el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft,
  ClipboardCheck,
  Clock3,
  HelpCircle,
  ListFilter,
  MessageSquare,
  MonitorUp,
  Tag
} from 'lucide-vue-next'
import { examApi } from '@/api'
import MarkdownAnswer from '@/components/exam/MarkdownAnswer.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const resultData = ref(null)
const activeFilter = ref('all')

const fetchResult = async () => {
  loading.value = true
  try {
    resultData.value = await examApi.getExamResult(route.params.recordId)
  } catch {
    ElMessage.error('获取答卷结果失败')
  } finally {
    loading.value = false
  }
}

const questionRows = computed(() => (resultData.value?.details || []).map((item, index) => ({
  item,
  number: index + 1
})))

const fullCount = computed(() => questionRows.value.filter(row => getQuestionState(row.item) === 'full').length)
const wrongCount = computed(() => questionRows.value.filter(row => getQuestionState(row.item) === 'wrong').length)
const partialCount = computed(() => questionRows.value.filter(row => getQuestionState(row.item) === 'partial').length)
const pendingCount = computed(() => questionRows.value.filter(row => getQuestionState(row.item) === 'pending').length)
const subjectiveCount = computed(() => questionRows.value.filter(row => isSubjective(row.item.question_type)).length)

const filterOptions = computed(() => [
  { value: 'all', label: '全部', count: questionRows.value.length },
  { value: 'wrong', label: '错题', count: wrongCount.value + partialCount.value },
  { value: 'pending', label: '待阅', count: pendingCount.value },
  { value: 'subjective', label: '主观题', count: subjectiveCount.value }
])

const filteredDetails = computed(() => {
  if (activeFilter.value === 'wrong') {
    return questionRows.value.filter(row => ['wrong', 'partial'].includes(getQuestionState(row.item)))
  }
  if (activeFilter.value === 'pending') {
    return questionRows.value.filter(row => getQuestionState(row.item) === 'pending')
  }
  if (activeFilter.value === 'subjective') {
    return questionRows.value.filter(row => isSubjective(row.item.question_type))
  }
  return questionRows.value
})

const recordStatusText = computed(() => {
  const record = resultData.value?.record
  if (record?.status !== 'GRADED') return '主观题阅卷中'
  return record.is_passed ? '已完成 · 通过' : '已完成 · 未通过'
})

const statusTone = computed(() => {
  const record = resultData.value?.record
  if (record?.status !== 'GRADED') return 'tone-pending'
  return record.is_passed ? 'tone-pass' : 'tone-fail'
})

const backLabel = computed(() => {
  if (route.query.from === 'grading') return '返回阅卷中心'
  if (route.query.from === 'analytics') return '返回考务分析'
  return '返回考务中心'
})

const getQuestionState = (item) => {
  if (!item.is_graded) return 'pending'
  const score = Number(item.actual_score || 0)
  const maxScore = Number(item.max_score || 0)
  if (maxScore > 0 && score >= maxScore) return 'full'
  if (score > 0) return 'partial'
  return 'wrong'
}

const getQuestionStatusLabel = (item) => {
  const state = getQuestionState(item)
  if (state === 'pending') return '待考官批阅'
  if (state === 'full') return `满分 · ${item.actual_score} 分`
  if (state === 'partial') return `${item.actual_score} / ${item.max_score} 分`
  return '0 分'
}

const jumpToQuestion = async (row) => {
  const visible = filteredDetails.value.some(entry => entry.item.id === row.item.id)
  if (!visible) activeFilter.value = 'all'
  await nextTick()
  document.getElementById(`question-${row.item.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const isOptionInAnswer = (optionValue, answer) => {
  if (answer === undefined || answer === null) return false
  return Array.isArray(answer) ? answer.includes(optionValue) : answer === optionValue
}

const getOptionClass = (optionValue, item) => {
  const correct = isOptionInAnswer(optionValue, item.correct_answer)
  const selected = isOptionInAnswer(optionValue, item.user_answer)
  return {
    'option-is-correct': correct,
    'option-is-selected': selected,
    'option-is-wrong': selected && !correct
  }
}

const formatAnswerText = (answer) => {
  if (answer === undefined || answer === null || answer === '' || (Array.isArray(answer) && !answer.length)) return '（未作答）'
  if (Array.isArray(answer)) return answer.join('、')
  if (typeof answer === 'boolean') return answer ? '正确 (True)' : '错误 (False)'
  if (answer === 'true') return '正确 (True)'
  if (answer === 'false') return '错误 (False)'
  if (typeof answer === 'object') return String(answer.content || '（仅上传了图片）')
  return String(answer)
}

const isSubjective = (type) => ['textarea', 'essay', 'subjective'].includes(String(type || '').toLowerCase())

const getTypeName = (type) => ({
  radio: '单选题',
  checkbox: '多选题',
  truefalse: '判断题',
  fillblank: '填空题',
  textarea: '简答题',
  essay: '简答题',
  subjective: '简答题'
})[String(type || '').toLowerCase()] || '题目'

const formatDuration = (seconds) => {
  const value = Number(seconds || 0)
  const minutes = Math.floor(value / 60)
  const remain = value % 60
  return minutes ? `${minutes}分${remain}秒` : `${remain}秒`
}

const formatDate = (value) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '—'

const backToList = () => {
  if (route.query.from === 'grading') router.push('/admin/grading')
  else if (route.query.from === 'analytics') router.push('/admin/analytics')
  else router.push('/student/exams')
}

onMounted(fetchResult)
</script>

<style scoped>
.result-page {
  min-height: 100vh;
  padding: 22px 28px 56px;
  color: #223247;
  background: #edf2f6;
}
.loading-state { padding: 120px 0; text-align: center; color: #8190a1; }
.loading-state p { margin-top: 10px; font-size: 13px; }
.document-toolbar {
  max-width: 1320px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.back-button {
  padding: 7px 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  border-radius: 6px;
  color: #52677e;
  background: transparent;
  cursor: pointer;
}
.back-button:hover { color: #245f8b; background: #e1eaf1; }
.back-button:focus-visible,
.filter-tabs button:focus-visible,
.question-grid button:focus-visible { outline: 2px solid #4c8db9; outline-offset: 2px; }
.archive-mark { display: flex; align-items: baseline; gap: 9px; color: #8a98a7; font-size: 10px; letter-spacing: .1em; }
.archive-mark strong { color: #4f6378; font-family: Consolas, monospace; font-size: 11px; }
.paper-masthead {
  max-width: 1320px;
  min-height: 190px;
  margin: 0 auto 18px;
  padding: 28px 34px;
  display: flex;
  align-items: stretch;
  justify-content: space-between;
  gap: 28px;
  border-top: 4px solid #245f8b;
  background: #fff;
  box-shadow: 0 8px 26px rgba(35, 54, 74, .07);
}
.masthead-copy { min-width: 0; flex: 1; }
.paper-eyebrow { display: flex; align-items: center; gap: 10px; color: #6f8193; font-size: 11px; letter-spacing: .04em; }
.paper-eyebrow i { width: 22px; height: 1px; background: #b8c4cf; }
.paper-masthead h1 {
  margin: 19px 0 24px;
  color: #17293b;
  font-family: 'STSong', 'SimSun', serif;
  font-size: clamp(25px, 3vw, 36px);
  font-weight: 700;
  letter-spacing: .03em;
}
.candidate-line { display: flex; gap: 42px; flex-wrap: wrap; }
.candidate-line > div { display: flex; align-items: baseline; gap: 8px; }
.candidate-line span { color: #8a98a7; font-size: 10px; }
.candidate-line strong { color: #34495e; font-size: 12px; }
.candidate-line small { color: #9aa7b4; font-size: 10px; }
.tone-pass { color: #187354 !important; }
.tone-fail { color: #b23a4a !important; }
.tone-pending { color: #a36b17 !important; }
.score-stamp {
  width: 155px;
  flex: 0 0 155px;
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid currentColor;
  outline: 1px solid currentColor;
  outline-offset: -6px;
  background: #fbfcfd;
  transform: rotate(-1deg);
}
.score-stamp span { font-size: 10px; letter-spacing: .14em; }
.score-stamp strong { margin: 5px 0 0; font-family: Georgia, serif; font-size: 44px; line-height: 1; }
.score-stamp small { font-size: 10px; opacity: .75; }
.score-stamp em { margin-top: 11px; padding-top: 8px; border-top: 1px solid currentColor; font-size: 11px; font-style: normal; font-weight: 700; }
.paper-workspace {
  max-width: 1320px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 276px;
  gap: 18px;
  align-items: start;
}
.paper-stream { min-width: 0; display: flex; flex-direction: column; gap: 13px; }
.stream-toolbar {
  min-height: 66px;
  padding: 13px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border: 1px solid #dce4ea;
  background: rgba(255, 255, 255, .92);
}
.stream-toolbar h2 { margin: 0; color: #263a4e; font-size: 14px; }
.stream-toolbar p { margin: 3px 0 0; color: #8b99a7; font-size: 10px; }
.filter-tabs { display: flex; align-items: center; gap: 3px; }
.filter-tabs button {
  padding: 6px 9px;
  border: 0;
  border-radius: 5px;
  color: #64778b;
  background: transparent;
  cursor: pointer;
  font-size: 11px;
}
.filter-tabs button span { margin-left: 3px; color: #9aa7b4; font-family: Consolas, monospace; }
.filter-tabs button:hover { background: #edf3f7; }
.filter-tabs button.active { color: #245f8b; background: #e6f0f6; font-weight: 700; }
.empty-filter { padding: 70px 20px; border: 1px dashed #cfd9e1; color: #8a99a8; background: #f8fafb; text-align: center; font-size: 12px; }
.question-sheet {
  scroll-margin-top: 14px;
  overflow: hidden;
  border: 1px solid #dce4ea;
  border-left: 4px solid #aebdca;
  background: #fff;
  box-shadow: 0 4px 14px rgba(36, 53, 72, .035);
}
.question-sheet.state-full { border-left-color: #2c8b69; }
.question-sheet.state-partial { border-left-color: #3f7ea7; }
.question-sheet.state-wrong { border-left-color: #c04a5a; }
.question-sheet.state-pending { border-left-color: #c18a2f; }
.question-heading {
  min-height: 65px;
  padding: 13px 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #e8edf1;
  background: #fafbfd;
}
.question-number { display: flex; align-items: center; gap: 11px; }
.question-number > span { color: #7b8da0; font-family: Georgia, serif; font-size: 27px; line-height: 1; }
.question-number div { display: flex; flex-direction: column; gap: 2px; }
.question-number strong { color: #2d4054; font-size: 12px; }
.question-number small { color: #929fad; font-size: 10px; }
.question-result { padding: 4px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; }
.result-full { color: #187354; background: #eaf7f1; }
.result-partial { color: #2c6e99; background: #eaf3f8; }
.result-wrong { color: #af3548; background: #fcecef; }
.result-pending { color: #9a691d; background: #fff5df; }
.question-content { padding: 21px 23px 17px; }
.question-content > h3 { margin: 0 0 18px; color: #172b3f; font-size: 14px; line-height: 1.75; }
.option-list { display: flex; flex-direction: column; gap: 7px; margin-bottom: 17px; }
.option-row {
  min-height: 42px;
  padding: 8px 11px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: 1px solid #e1e7ec;
  color: #526579;
  background: #fff;
  font-size: 12px;
}
.option-key { width: 24px; height: 24px; display: grid; place-items: center; border: 1px solid #cfd9e1; border-radius: 50%; font-weight: 700; }
.option-label { min-width: 0; flex: 1; }
.option-is-correct { border-color: #a9d6c5; background: #f1faf6; }
.option-is-selected { box-shadow: inset 3px 0 #397aa5; }
.option-is-wrong { border-color: #ebbac2; background: #fff5f6; box-shadow: inset 3px 0 #c04a5a; }
.choice-mark { padding: 2px 5px; border-radius: 3px; font-size: 9px; white-space: nowrap; }
.user-choice { color: #2f6f99; background: #e5f0f7; }
.correct-choice { color: #187354; background: #e5f5ed; }
.section-caption { margin-bottom: 7px; display: flex; align-items: center; gap: 5px; color: #718295; font-size: 10px; font-weight: 700; letter-spacing: .04em; }
.answer-paper {
  min-height: 105px;
  padding: 15px 17px;
  border: 1px solid #dce4ea;
  color: #283d51;
  background: repeating-linear-gradient(#fff 0, #fff 30px, #edf1f4 31px);
  font-size: 13px;
}
.reference-line { margin-top: 10px; padding: 10px 12px; display: grid; grid-template-columns: 68px 1fr; gap: 10px; background: #f2f8f5; }
.reference-line span { color: #398064; font-size: 10px; font-weight: 700; }
.reference-line p { margin: 0; color: #315c4c; font-size: 11px; line-height: 1.65; }
.objective-comparison { display: grid; grid-template-columns: 1fr 1fr; border: 1px solid #e1e7ec; }
.objective-comparison > div { min-height: 55px; padding: 10px 13px; display: flex; flex-direction: column; gap: 5px; }
.objective-comparison > div + div { border-left: 1px solid #e1e7ec; }
.objective-comparison span { color: #8b98a6; font-size: 9px; }
.objective-comparison strong { font-family: Consolas, monospace; font-size: 12px; }
.answer-correct { color: #187354; }
.answer-wrong { color: #b23a4a; }
.explanation-box,
.teacher-note { margin-top: 12px; padding: 11px 13px; border-left: 2px solid #6b9abb; background: #f2f7fa; }
.teacher-note { border-left-color: #c18a2f; background: #fff9eb; }
.explanation-box p,
.teacher-note p { margin: 0; color: #4a6074; font-size: 11px; line-height: 1.7; }
.teacher-note p { color: #76571f; }
.question-footer { padding: 9px 18px; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #edf1f4; color: #8695a4; background: #fbfcfd; font-size: 10px; }
.question-footer span { display: flex; align-items: center; gap: 4px; }
.question-footer strong { color: #334d63; font-size: 12px; }
.paper-sidebar { position: sticky; top: 14px; display: flex; flex-direction: column; gap: 12px; }
.sidebar-card { border: 1px solid #d8e1e8; background: #fff; box-shadow: 0 4px 14px rgba(36, 53, 72, .04); }
.sidebar-title { padding: 12px 14px; display: flex; align-items: center; gap: 7px; border-bottom: 1px solid #e6ebef; color: #334b61; font-size: 12px; font-weight: 700; }
.score-breakdown { padding: 5px 14px; }
.score-breakdown > div { padding: 9px 0; display: flex; align-items: baseline; justify-content: space-between; border-bottom: 1px dashed #dde4ea; }
.score-breakdown span { color: #7f8f9f; font-size: 10px; }
.score-breakdown strong { color: #354d63; font-size: 12px; }
.score-breakdown .receipt-total { border-bottom: 0; }
.score-breakdown .receipt-total strong { color: #245f8b; font-family: Georgia, serif; font-size: 20px; }
.exam-metrics { padding: 10px 14px; display: flex; justify-content: space-between; border-top: 1px solid #e8edf1; background: #f8fafb; }
.exam-metrics span { display: flex; align-items: center; gap: 4px; color: #728496; font-size: 9px; }
.exam-metrics span.warning { color: #a36b17; }
.question-grid { padding: 14px; display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; }
.question-grid button { aspect-ratio: 1; border: 1px solid #d3dde4; border-radius: 4px; color: #617487; background: #f8fafb; cursor: pointer; font-size: 10px; }
.question-grid button:hover { transform: translateY(-1px); box-shadow: 0 3px 7px rgba(35, 54, 74, .11); }
.question-grid .map-full { border-color: #8ac2ac; color: #176a4e; background: #e9f7f0; }
.question-grid .map-partial { border-color: #9fc4dc; color: #2c6e99; background: #eaf3f8; }
.question-grid .map-wrong { border-color: #e1a5ae; color: #a93042; background: #fcedef; }
.question-grid .map-pending { border-color: #dfc17e; color: #93621a; background: #fff4dd; }
.map-legend { padding: 10px 14px 13px; display: grid; grid-template-columns: 1fr 1fr; gap: 7px 10px; border-top: 1px solid #e8edf1; }
.map-legend span { display: flex; align-items: center; gap: 5px; color: #8291a1; font-size: 9px; }
.map-legend i { width: 7px; height: 7px; border-radius: 2px; }
.legend-full { background: #50a382; }
.legend-partial { background: #6099bd; }
.legend-wrong { background: #c65b69; }
.legend-pending { background: #c99a43; }
.security-card { max-width: 760px; margin: 50px auto; padding: 55px 30px; border: 1px solid #dae2e8; background: #fff; text-align: center; }
.security-icon { width: 60px; height: 60px; margin: 0 auto 18px; display: grid; place-items: center; border: 1px solid #9ba9b6; border-radius: 50%; color: #687b8e; font-size: 11px; }
.security-card h3 { margin: 0 0 7px; color: #30475d; font-size: 16px; }
.security-card p { margin: 0 auto 22px; max-width: 480px; color: #8291a1; font-size: 12px; line-height: 1.7; }
@media (max-width: 980px) {
  .result-page { padding: 16px 16px 40px; }
  .paper-workspace { grid-template-columns: 1fr; }
  .paper-sidebar { position: static; display: grid; grid-template-columns: 1fr 1fr; grid-row: 1; }
}
@media (max-width: 680px) {
  .paper-masthead { padding: 22px 20px; flex-direction: column; }
  .score-stamp { width: 100%; flex-basis: auto; transform: none; }
  .candidate-line { gap: 13px 24px; }
  .stream-toolbar { align-items: flex-start; flex-direction: column; }
  .filter-tabs { width: 100%; overflow-x: auto; }
  .question-content { padding: 17px 15px 14px; }
  .question-heading { padding: 12px 14px; }
  .objective-comparison { grid-template-columns: 1fr; }
  .objective-comparison > div + div { border-left: 0; border-top: 1px solid #e1e7ec; }
  .paper-sidebar { display: flex; }
  .question-grid { grid-template-columns: repeat(8, 1fr); }
}

/* 与系统现有卡片语言对齐：保留整卷工作区结构，弱化纸质档案感。 */
.result-page {
  padding: 24px 30px 56px;
  color: var(--text-main);
  background: var(--bg-main);
}
.back-button {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-muted);
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.back-button:hover { color: var(--primary-hover); border-color: #bfdbfe; background: #eff6ff; }
.archive-mark {
  padding: 5px 9px;
  border-radius: 6px;
  color: #94a3b8;
  background: #eef2f7;
  letter-spacing: 0;
}
.archive-mark strong { color: #64748b; }
.paper-masthead {
  min-height: 170px;
  padding: 26px 30px;
  border: 1px solid var(--border-color);
  border-top: 1px solid var(--border-color);
  border-radius: 14px;
  box-shadow: var(--shadow-sm);
}
.paper-eyebrow { color: #64748b; letter-spacing: 0; }
.paper-eyebrow span:first-child {
  padding: 4px 8px;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  color: #2563eb;
  background: #eff6ff;
  font-weight: 650;
}
.paper-eyebrow i { background: #dbe3ec; }
.paper-masthead h1 {
  margin: 17px 0 22px;
  color: #0f172a;
  font-family: inherit;
  font-size: clamp(23px, 2.5vw, 30px);
  letter-spacing: 0;
}
.candidate-line span { color: #94a3b8; }
.candidate-line strong { color: #334155; }
.score-stamp {
  width: 174px;
  flex-basis: 174px;
  padding: 18px 16px;
  border: 1px solid #bfdbfe;
  outline: 0;
  border-radius: 12px;
  color: #2563eb !important;
  background: #eff6ff;
  transform: none;
}
.score-stamp.tone-pass { color: #059669 !important; border-color: #a7f3d0; background: #ecfdf5; }
.score-stamp.tone-fail { color: #e11d48 !important; border-color: #fecdd3; background: #fff1f2; }
.score-stamp.tone-pending { color: #d97706 !important; border-color: #fde68a; background: #fffbeb; }
.score-stamp strong { font-family: inherit; font-size: 40px; font-weight: 800; }
.score-stamp em { border-top-color: currentColor; }
.paper-workspace { gap: 20px; }
.stream-toolbar {
  padding: 14px 18px;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.stream-toolbar h2 { color: #1e293b; font-size: 15px; }
.filter-tabs { padding: 3px; border-radius: 8px; background: #f1f5f9; }
.filter-tabs button { border-radius: 6px; color: #64748b; }
.filter-tabs button.active { color: #2563eb; background: #fff; box-shadow: 0 1px 3px rgba(15, 23, 42, .08); }
.question-sheet {
  border: 1px solid var(--border-color);
  border-left-width: 4px;
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
}
.question-heading { padding: 14px 18px; background: #f8fafc; }
.question-number > span {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 9px;
  color: #2563eb;
  background: #eff6ff;
  font-family: inherit;
  font-size: 14px;
  font-weight: 750;
}
.question-number strong { color: #1e293b; font-size: 13px; }
.question-result { padding: 4px 9px; border-radius: 999px; }
.question-content > h3 { color: #1e293b; }
.option-row { border-radius: 8px; }
.option-key { border-radius: 6px; }
.answer-paper {
  border-radius: 8px;
  background: #f8fafc;
}
.reference-line { border: 1px solid #d1fae5; border-radius: 8px; background: #ecfdf5; }
.objective-comparison { overflow: hidden; border-radius: 8px; background: #f8fafc; }
.explanation-box,
.teacher-note { border-radius: 8px; }
.question-footer { background: #f8fafc; }
.sidebar-card {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.sidebar-title { color: #334155; background: #f8fafc; }
.score-breakdown .receipt-total strong { color: #2563eb; font-family: inherit; font-weight: 800; }
.question-grid button { border-radius: 6px; }
.security-card { border-radius: 14px; box-shadow: var(--shadow-sm); }
@media (max-width: 980px) {
  .result-page { padding: 16px 16px 40px; }
}
@media (max-width: 680px) {
  .paper-masthead { padding: 22px 20px; }
  .score-stamp { width: 100%; flex-basis: auto; }
}
@media print {
  .result-page { padding: 0; background: #fff; }
  .document-toolbar,
  .paper-sidebar,
  .stream-toolbar { display: none; }
  .paper-workspace { display: block; }
  .paper-masthead { box-shadow: none; }
  .question-sheet { break-inside: avoid; box-shadow: none; }
}
</style>
