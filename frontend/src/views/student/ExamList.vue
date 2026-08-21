<template>
  <AppPage class="exam-list-container">
    <AppPageHeader
      eyebrow="学习与考试"
      :title="`你好，${userStore.fullName}`"
      :description="`所属部门：${userStore.deptName} · 企业在线考试与能力评测中心`"
    >
      <template #actions>
        <div class="stat-pill">
          <span class="num">{{ examList.length }}</span>
          <span class="label">可参与考试</span>
        </div>
      </template>
    </AppPageHeader>

    <AppPanel
      title="考务任务列表"
      description="请在截止时间前参加作答，考试期间请遵守考场纪律"
    >
      <AppState v-if="loading" loading loading-text="正在加载考务数据..." />

      <AppState
        v-else-if="examList.length === 0"
        title="当前暂无发布的考试安排"
        description="管理员发布新的考核任务后将在此处显示"
      />

      <div v-else class="exam-grid">
      <div v-for="exam in examList" :key="exam.id" class="exam-card app-card">
        <div class="card-top">
          <div class="title-row">
            <h4 class="exam-title">{{ exam.title }}</h4>
            <a-tag :color="getStatusTagColor(exam)" size="small">
              {{ getStatusText(exam) }}
            </a-tag>
          </div>
          <p class="exam-desc">{{ exam.description || '暂无描述' }}</p>
        </div>

        <div class="card-meta-list">
          <div class="meta-item time-item">
            <span class="meta-label flex items-center">
              <Clock :size="13" class="mr-1 text-blue-500" />
              考务开放时间:
            </span>
            <span class="meta-val font-medium text-blue-700">
              {{ formatTimeRange(exam.start_time, exam.end_time) }}
            </span>
          </div>
          <div class="meta-item">
            <span class="meta-label">试卷总分/及格线:</span>
            <span class="meta-val font-semibold text-slate-800">{{ exam.total_score }}分 / {{ exam.pass_score }}分</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">答题限时:</span>
            <span class="meta-val">{{ exam.duration_minutes }} 分钟</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">作答次数:</span>
            <span class="meta-val">已考 {{ exam.user_attempt_count }} 次 (限 {{ exam.max_retries }} 次)</span>
          </div>
          <div class="meta-item" v-if="exam.latest_score !== null">
            <span class="meta-label">最近一次得分:</span>
            <span class="meta-val score-highlight" :class="exam.latest_score >= exam.pass_score ? 'text-green-600' : 'text-amber-600'">
              {{ exam.latest_score }} 分
            </span>
          </div>
        </div>

        <div class="card-actions">
          <!-- 1. 未到开放时间 -->
          <a-button
            v-if="getTimeStatus(exam).code === 'NOT_STARTED'"
            type="secondary"
            disabled 
            class="action-btn"
          >
            尚未开放 ({{ formatShortTime(exam.start_time) }} 开启)
          </a-button>

          <!-- 2. 已过截止时间且无进行中记录 -->
          <a-button
            v-else-if="getTimeStatus(exam).code === 'EXPIRED' && exam.latest_record_status !== 'IN_PROGRESS'"
            type="secondary"
            disabled 
            class="action-btn"
          >
            考务已截止
          </a-button>

          <!-- 3. 正常允许作答或重考 -->
          <a-button
            v-else-if="canTakeExam(exam)"
            type="primary" 
            class="action-btn"
            @click="startExam(exam.id)"
          >
            {{ exam.latest_record_status === 'IN_PROGRESS' ? '继续作答' : '开始考试' }}
          </a-button>

          <!-- 4. 已交卷但待人工阅卷 -->
          <a-button
            v-else-if="exam.latest_record_status === 'SUBMITTED'"
            type="outline"
            status="warning"
            disabled 
            class="action-btn"
          >
            <Hourglass :size="14" class="mr-1" /> 主观题批阅中
          </a-button>

          <!-- 5. 已完成出分 -->
          <a-button
            v-if="exam.latest_record_id && exam.latest_record_status === 'GRADED'"
            type="outline"
            status="success"
            class="action-btn"
            @click="viewResult(exam.latest_record_id)"
          >
            <ChartColumnBig :size="14" class="mr-1" /> 查看成绩与解析
          </a-button>
        </div>
      </div>
      </div>
    </AppPanel>
  </AppPage>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { examApi } from '@/api'
import { Hourglass, ChartColumnBig, Clock } from 'lucide-vue-next'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppState from '@/components/ui/AppState.vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(true)
const examList = ref([])

const fetchExams = async () => {
  loading.value = true
  try {
    const res = await examApi.getExamTasks()
    examList.value = res
  } catch (e) {
    //
  } finally {
    loading.value = false
  }
}

const formatShortTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const pad = n => n.toString().padStart(2, '0')
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const formatTimeRange = (start, end) => {
  if (!start && !end) return '永久有效 (随时可考)'
  const fmt = (t) => {
    if (!t) return ''
    const d = new Date(t)
    const pad = n => n.toString().padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
  }
  if (start && end) {
    return `${fmt(start)} 至 ${fmt(end)}`
  }
  if (start) return `自 ${fmt(start)} 起开放`
  return `截止至 ${fmt(end)}`
}

const getTimeStatus = (exam) => {
  const now = new Date().getTime()
  if (exam.start_time) {
    const start = new Date(exam.start_time).getTime()
    if (now < start) return { code: 'NOT_STARTED', text: '未开放', type: 'info' }
  }
  if (exam.end_time) {
    const end = new Date(exam.end_time).getTime()
    if (now > end) return { code: 'EXPIRED', text: '已截止', type: 'danger' }
  }
  return { code: 'ACTIVE', text: '进行中', type: 'success' }
}

const canTakeExam = (exam) => {
  if (exam.latest_record_status === 'IN_PROGRESS') return true
  return exam.user_attempt_count < exam.max_retries
}

const getStatusText = (exam) => {
  if (exam.latest_record_status === 'IN_PROGRESS') return '作答中'
  if (exam.latest_record_status === 'SUBMITTED') return '待阅卷'
  if (exam.latest_record_status === 'GRADED') {
    return exam.latest_score >= exam.pass_score ? '已及格' : '未及格'
  }
  const timeStat = getTimeStatus(exam)
  if (timeStat.code === 'NOT_STARTED') return '未开放'
  if (timeStat.code === 'EXPIRED') return '已截止'
  return '未参加'
}

const getStatusTagColor = (exam) => {
  if (exam.latest_record_status === 'IN_PROGRESS') return 'blue'
  if (exam.latest_record_status === 'SUBMITTED') return 'orange'
  if (exam.latest_record_status === 'GRADED') {
    return exam.latest_score >= exam.pass_score ? 'green' : 'red'
  }
  const timeStat = getTimeStatus(exam)
  if (timeStat.type === 'danger') return 'red'
  if (timeStat.type === 'success') return 'green'
  return 'gray'
}

const startExam = (examId) => {
  router.push(`/exam/take/${examId}`)
}

const viewResult = (recordId) => {
  router.push(`/exam/result/${recordId}`)
}

onMounted(() => {
  fetchExams()
})
</script>

<style scoped>
.exam-list-container {
  --app-page-gap: var(--app-space-4);
}

.stat-pill {
  background: white;
  padding: 10px 20px;
  border: 1px solid var(--color-border-2);
  border-radius: var(--app-radius-control);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stat-pill .num {
  font-size: 22px;
  font-weight: 800;
  color: #2563eb;
}
.stat-pill .label {
  font-size: 11px;
  color: #64748b;
}

.section-title {
  margin-bottom: 18px;
}
.section-title h3 {
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}
.sub-tip {
  font-size: 12px;
  color: #94a3b8;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: var(--app-space-4);
}

.exam-card {
  background: white;
  padding: var(--app-space-5);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border-radius: var(--app-radius-panel);
}

.title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
}
.exam-title {
  font-size: 15.5px;
  font-weight: 700;
  color: var(--color-text-1);
  line-height: 1.4;
}
.exam-desc {
  font-size: 12.5px;
  color: var(--color-text-3);
  margin-bottom: 16px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta-list {
  background: var(--color-fill-1);
  border-radius: var(--app-radius-control);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 18px;
}
.meta-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.time-item {
  padding-bottom: 5px;
  margin-bottom: 2px;
  border-bottom: 1px dashed #e2e8f0;
}
.meta-label {
  color: #64748b;
}
.meta-val {
  color: #334155;
}
.score-highlight {
  font-weight: 700;
  font-size: 13px;
}

.card-actions {
  display: flex;
  gap: 10px;
}
.action-btn {
  flex: 1;
  font-weight: 600;
}
@media (max-width: 720px) {
  .exam-grid { grid-template-columns: minmax(0, 1fr); }
  .exam-card { min-width: 0; padding: var(--app-space-4); }
  .meta-item { gap: var(--app-space-2); align-items: flex-start; }
  .meta-label { flex: 0 0 auto; }
  .meta-val { min-width: 0; text-align: right; overflow-wrap: anywhere; }
  .card-actions { flex-wrap: wrap; }
  .action-btn { flex-basis: 100%; }
}
</style>
