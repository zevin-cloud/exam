<template>
  <AppPage class="analytics-container">
    <AppPageHeader
      eyebrow="数据中心"
      title="考务数据概览"
      description="从参与、成绩、组织与知识四个维度定位考务风险"
    >
      <template #icon>
          <BarChart3 :size="20" class="text-blue-600" />
      </template>
      <template #actions>
        <div class="filter-group">
          <span class="filter-label">分析范围</span>
          <a-select
            v-model="selectedExamId"
            placeholder="全部考试汇总"
            class="exam-select-box"
            @change="handleExamChange"
          >
            <a-option :value="null" label="全部考试汇总" />
            <a-option
              v-for="task in examTasks"
              :key="task.id"
              :label="`#${task.id} ${task.title}`"
              :value="task.id"
            />
          </a-select>
        </div>

        <a-button type="primary" @click="refreshAll" :loading="loading">
          <template #icon><icon-refresh /></template>刷新数据
        </a-button>
      </template>
    </AppPageHeader>

    <!-- 加载中 -->
    <AppState v-if="loading" loading loading-text="正在汇总分析考务数据..." />

    <template v-else-if="dashboardData">
      <section class="overview-panel app-card">
        <div class="overview-heading">
          <div>
            <h2>考试概况</h2>
            <p>关键指标与参考情况</p>
          </div>
          <span class="overview-status"><i></i> 数据已更新</span>
        </div>

        <div class="overview-grid">
          <article class="overview-tile tile-blue">
            <div class="tile-copy">
              <span>参考率</span>
              <strong>{{ attendanceRate }}<small>%</small></strong>
              <p>应考 {{ dashboardData.overview.total_eligible }} 人 · 缺考 {{ dashboardData.overview.total_absent }} 人</p>
            </div>
            <svg class="sparkline" viewBox="0 0 132 62" aria-hidden="true">
              <path d="M2 43 C14 9 18 55 30 31 S48 17 58 38 S75 53 84 25 S103 11 112 34 S124 44 130 17" />
            </svg>
          </article>

          <article class="overview-tile tile-green">
            <div class="tile-copy">
              <span>有效答卷</span>
              <strong>{{ dashboardData.overview.total_takers }}<small>份</small></strong>
              <p>已完成并进入统计的答卷</p>
            </div>
            <div class="mini-bars" aria-hidden="true">
              <i v-for="height in [34, 52, 27, 62, 43, 70, 38, 57, 47]" :key="height" :style="{ height: `${height}px` }"></i>
            </div>
          </article>

          <article class="overview-tile tile-cyan">
            <div class="tile-copy">
              <span>平均得分</span>
              <strong>{{ dashboardData.overview.avg_score }}<small>分</small></strong>
              <p>最高 {{ dashboardData.overview.max_score }} · 最低 {{ dashboardData.overview.min_score }}</p>
            </div>
            <svg class="sparkline" viewBox="0 0 132 62" aria-hidden="true">
              <path d="M2 18 C10 48 22 47 29 27 S44 13 51 39 S67 53 75 25 S90 19 98 41 S117 48 130 15" />
            </svg>
          </article>

          <article class="overview-tile tile-violet">
            <div class="tile-copy">
              <span>综合及格率</span>
              <strong>{{ dashboardData.overview.pass_rate }}<small>%</small></strong>
              <p>{{ healthLabel }} · 成绩极差 {{ scoreSpread }} 分</p>
            </div>
            <div class="pass-ring" :style="{ '--rate': `${dashboardData.overview.pass_rate * 3.6}deg` }" aria-hidden="true">
              <span></span>
            </div>
          </article>
        </div>
      </section>

      <!-- 可检索、可导出的成绩台账 -->
      <div class="app-card section-card score-ledger">
        <div class="ledger-heading">
          <div>
            <div class="ledger-eyebrow"><SlidersHorizontal :size="13" /> 成绩检索台账</div>
            <h3 class="section-title ledger-title">按人员、部门、成绩与时间交叉检索</h3>
            <p class="section-subtitle">只统计每位考生每场考试最后一次有效答卷，当前筛选条件会原样应用到 Excel 导出。</p>
          </div>
          <a-button type="primary" :loading="exporting" @click="exportScores">
            <Download :size="15" /> 导出当前结果
          </a-button>
        </div>

        <div class="filter-rail">
          <div class="filter-field filter-keyword">
            <label>考生 / 账号 / 考试</label>
            <a-input v-model="scoreFilters.keyword" allow-clear placeholder="输入姓名、账号或考试名称" @press-enter="searchScores" />
          </div>
          <div class="filter-field">
            <label>所属部门（含下级）</label>
            <a-select v-model="scoreFilters.department_id" allow-clear allow-search placeholder="全部部门">
              <a-option v-for="dept in departments" :key="dept.id" :label="dept.name" :value="dept.id" />
            </a-select>
          </div>
          <div class="filter-field">
            <label>成绩状态</label>
            <a-select v-model="scoreFilters.result_status">
              <a-option label="全部有效答卷" value="all" />
              <a-option label="及格" value="passed" />
              <a-option label="未及格" value="failed" />
              <a-option label="主观题待阅卷" value="pending" />
            </a-select>
          </div>
          <div class="filter-field score-range-field">
            <label>分数区间</label>
            <div class="range-inputs">
              <a-input-number v-model="scoreFilters.score_min" :min="0" :max="999" :hide-button="true" placeholder="最低" />
              <span>—</span>
              <a-input-number v-model="scoreFilters.score_max" :min="0" :max="999" :hide-button="true" placeholder="最高" />
            </div>
          </div>
          <div class="filter-field date-filter-field">
            <label>交卷时间</label>
            <a-range-picker
              v-model="scoreFilters.date_range"
              value-format="YYYY-MM-DD HH:mm:ss"
              show-time
              :placeholder="['开始时间', '结束时间']"
            />
          </div>
          <div class="filter-field">
            <label>排序方式</label>
            <a-select v-model="scoreFilters.sort_by">
              <a-option label="最近交卷" value="submit_desc" />
              <a-option label="成绩从高到低" value="score_desc" />
              <a-option label="成绩从低到高" value="score_asc" />
              <a-option label="用时最短" value="duration_asc" />
              <a-option label="用时最长" value="duration_desc" />
            </a-select>
          </div>
          <div class="filter-actions">
            <a-button type="primary" @click="searchScores"><Search :size="15" /> 查询成绩</a-button>
            <a-button @click="resetScoreFilters"><RotateCcw :size="14" /> 重置</a-button>
          </div>
        </div>

        <div class="ledger-summary">
          <div><span>命中答卷</span><strong>{{ scoreData.summary.matched_count }}</strong></div>
          <div><span>已出分</span><strong>{{ scoreData.summary.scored_count }}</strong></div>
          <div><span>待阅卷</span><strong class="summary-amber">{{ scoreData.summary.pending_count }}</strong></div>
          <div><span>及格人数</span><strong class="summary-green">{{ scoreData.summary.passed_count }}</strong></div>
          <div><span>筛选后均分</span><strong class="summary-blue">{{ scoreData.summary.avg_score }}</strong></div>
        </div>

        <a-table
          :columns="scoreColumns"
          :data="scoreData.items"
          :loading="scoreLoading"
          :pagination="false"
          row-key="record_id"
          stripe
          size="small"
        >
          <template #student="{ record: row }">
            <div class="student-cell">
              <strong>{{ row.student_name }}</strong>
              <span>{{ row.username }} · 第 {{ row.attempt_no }} 次</span>
            </div>
          </template>
          <template #score="{ record: row }">
            <div v-if="row.status === 'GRADED'" class="score-cell">
              <strong>{{ row.total_score }} 分</strong>
              <span>客观 {{ row.objective_score }} / 主观 {{ row.subjective_score }}</span>
            </div>
            <div v-else class="score-cell is-pending">
              <strong>待出分</strong>
              <span>客观题暂计 {{ row.objective_score }} 分</span>
            </div>
          </template>
          <template #result="{ record: row }">
            <a-tag v-if="row.status !== 'GRADED'" color="orange" size="small">待阅卷</a-tag>
            <a-tag v-else :color="row.is_passed ? 'green' : 'red'" size="small">
              {{ row.is_passed ? '及格' : '未及格' }}
            </a-tag>
          </template>
          <template #duration="{ record: row }">
            <span class="mono-cell">{{ formatDuration(row.duration_seconds) }}</span>
          </template>
          <template #submitted="{ record: row }">
            <span class="date-cell">{{ formatDate(row.submit_time) }}</span>
          </template>
          <template #operations="{ record: row }">
            <a-button type="text" size="mini" @click="viewPaper(row)">查看整卷</a-button>
          </template>
        </a-table>

        <div class="ledger-pagination">
          <span>共 {{ scoreData.total }} 条</span>
          <a-pagination
            :current="scorePage"
            :page-size="scorePageSize"
            :page-size-options="[10, 20, 50, 100]"
            :total="scoreData.total"
            show-page-size
            @change="handleScorePageChange"
            @page-size-change="handleScorePageSizeChange"
          />
        </div>
      </div>
    </template>
  </AppPage>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { analyticsApi, examApi, userApi } from '@/api'
import {
  BarChart3, Download, RotateCcw, Search, SlidersHorizontal
} from 'lucide-vue-next'
import { Message } from '@arco-design/web-vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppState from '@/components/ui/AppState.vue'

const loading = ref(true)
const dashboardData = ref(null)
const examTasks = ref([])
const selectedExamId = ref(null)
const router = useRouter()
const departments = ref([])
const scoreLoading = ref(false)
const exporting = ref(false)
const scorePage = ref(1)
const scorePageSize = ref(20)
const scoreColumns = [
  { title: '考生', minWidth: 165, fixed: 'left', slotName: 'student' },
  { title: '所属部门', dataIndex: 'department_name', minWidth: 140, ellipsis: true, tooltip: true },
  { title: '考试场次', dataIndex: 'exam_title', minWidth: 210, ellipsis: true, tooltip: true },
  { title: '成绩构成', width: 160, align: 'center', slotName: 'score' },
  { title: '结果', width: 105, align: 'center', slotName: 'result' },
  { title: '作答用时', width: 110, align: 'center', slotName: 'duration' },
  { title: '切屏', dataIndex: 'screen_switch_count', width: 72, align: 'center' },
  { title: '交卷时间', minWidth: 170, align: 'center', slotName: 'submitted' },
  { title: '操作', width: 95, align: 'center', fixed: 'right', slotName: 'operations' }
]
const defaultScoreFilters = () => ({
  keyword: '',
  department_id: null,
  result_status: 'all',
  score_min: null,
  score_max: null,
  date_range: [],
  sort_by: 'submit_desc'
})
const scoreFilters = ref(defaultScoreFilters())
const scoreData = ref({
  items: [],
  total: 0,
  summary: { matched_count: 0, scored_count: 0, pending_count: 0, passed_count: 0, avg_score: 0 }
})

const overview = computed(() => dashboardData.value?.overview || {})
const attendanceRate = computed(() => {
  const eligible = Number(overview.value.total_eligible || 0)
  if (!eligible) return 0
  return Math.min(100, Math.round(Number(overview.value.total_takers || 0) / eligible * 100))
})
const scoreSpread = computed(() => Math.max(0, Number(overview.value.max_score || 0) - Number(overview.value.min_score || 0)))
const healthTone = computed(() => {
  const rate = Number(overview.value.pass_rate || 0)
  if (rate >= 80) return 'good'
  if (rate >= 60) return 'watch'
  return 'risk'
})
const healthLabel = computed(() => ({ good: '运行良好', watch: '需要关注', risk: '存在风险' })[healthTone.value])

const fetchExamTasks = async () => {
  try {
    const res = await examApi.getTasks()
    examTasks.value = res
  } catch (e) {
    //
  }
}

const fetchDepartments = async () => {
  try {
    departments.value = await userApi.getDepartments()
  } catch {
    // 部门筛选不可用时仍可按其他维度查询。
  }
}

const fetchDashboard = async () => {
  loading.value = true
  try {
    const res = await analyticsApi.getDashboard(selectedExamId.value)
    dashboardData.value = res
  } catch (e) {
    // 拦截器已统一提示详细错误
  } finally {
    loading.value = false
  }
}

const buildScoreParams = () => {
  const filters = scoreFilters.value
  const params = {
    page: scorePage.value,
    page_size: scorePageSize.value,
    result_status: filters.result_status,
    sort_by: filters.sort_by
  }
  if (selectedExamId.value) params.exam_task_id = selectedExamId.value
  if (filters.department_id) params.department_id = filters.department_id
  if (filters.keyword?.trim()) params.keyword = filters.keyword.trim()
  if (filters.score_min !== null && filters.score_min !== undefined) params.score_min = filters.score_min
  if (filters.score_max !== null && filters.score_max !== undefined) params.score_max = filters.score_max
  if (filters.date_range?.length === 2) {
    params.submitted_from = filters.date_range[0]
    params.submitted_to = filters.date_range[1]
  }
  return params
}

const fetchScores = async () => {
  scoreLoading.value = true
  try {
    scoreData.value = await analyticsApi.searchScores(buildScoreParams())
  } finally {
    scoreLoading.value = false
  }
}

const searchScores = () => {
  if (!validateScoreRange()) return
  scorePage.value = 1
  fetchScores()
}

const validateScoreRange = () => {
  const { score_min: min, score_max: max } = scoreFilters.value
  if (min !== null && max !== null && min > max) {
    Message.warning('最低分不能高于最高分')
    return false
  }
  return true
}

const resetScoreFilters = () => {
  scoreFilters.value = defaultScoreFilters()
  scorePage.value = 1
  fetchScores()
}

const handleExamChange = () => {
  scorePage.value = 1
  fetchDashboard()
  fetchScores()
}

const refreshAll = () => {
  fetchDashboard()
  fetchScores()
}

const exportScores = async () => {
  if (!validateScoreRange()) return
  exporting.value = true
  try {
    const params = buildScoreParams()
    delete params.page
    delete params.page_size
    const blob = await analyticsApi.exportScores(params)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[-:T]/g, '')
    anchor.href = url
    anchor.download = `考试成绩明细_${timestamp}.xlsx`
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
    Message.success(`已导出 ${scoreData.value.summary.matched_count} 条成绩记录`)
  } finally {
    exporting.value = false
  }
}

const viewPaper = (row) => {
  router.push({ path: `/exam/result/${row.record_id}`, query: { from: 'analytics' } })
}

const handleScorePageChange = (page) => {
  scorePage.value = page
  fetchScores()
}

const handleScorePageSizeChange = (pageSize) => {
  scorePageSize.value = pageSize
  scorePage.value = 1
  fetchScores()
}

const formatDuration = (secs) => {
  if (!secs) return '0秒'
  const m = Math.floor(secs / 60)
  const s = secs % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

const formatDate = (isoStr) => {
  if (!isoStr) return '-'
  return new Date(isoStr).toLocaleString()
}

onMounted(() => {
  fetchExamTasks()
  fetchDepartments()
  fetchDashboard()
  fetchScores()
})
</script>

<style scoped>
.analytics-container {
  --app-page-gap: var(--app-space-4);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.filter-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}
.exam-select-box {
  width: 240px;
}

/* 参考数据分析台：安静的容器里用四种低饱和色区分指标类型。 */
.overview-panel {
  padding: 16px;
  border-radius: 2px;
}
.overview-heading {
  min-height: 46px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}
.overview-heading h2 {
  margin: 0;
  color: #1d2939;
  font-size: 16px;
  font-weight: 600;
}
.overview-heading p {
  margin-top: 3px;
  color: #98a2b3;
  font-size: 11px;
}
.overview-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #667085;
  font-size: 11px;
}
.overview-status i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #32b768;
  box-shadow: 0 0 0 3px rgba(50, 183, 104, .12);
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.overview-tile {
  min-width: 0;
  min-height: 134px;
  padding: 18px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  overflow: hidden;
  border-radius: 3px;
}
.tile-blue { background: #edf7ff; }
.tile-green { background: #eefbee; }
.tile-cyan { background: #eef8fc; }
.tile-violet { background: #f3f1ff; }
.tile-copy { min-width: 105px; }
.tile-copy > span {
  display: block;
  color: #344054;
  font-size: 13px;
  font-weight: 600;
}
.tile-copy strong {
  margin: 12px 0 7px;
  display: block;
  color: #101828;
  font-size: 29px;
  font-weight: 500;
  line-height: 1;
  letter-spacing: -.03em;
}
.tile-copy strong small {
  margin-left: 3px;
  color: #475467;
  font-size: 12px;
  font-weight: 500;
}
.tile-copy p {
  overflow: hidden;
  color: #7d8998;
  font-size: 10px;
  line-height: 1.45;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.sparkline {
  width: 42%;
  min-width: 92px;
  overflow: visible;
}
.sparkline path {
  fill: none;
  stroke: #629bff;
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-dasharray: 8 6;
}
.tile-cyan .sparkline path { stroke: #3db1dd; }
.mini-bars {
  height: 76px;
  display: flex;
  align-items: flex-end;
  gap: 7px;
}
.mini-bars i {
  width: 7px;
  display: block;
  border-radius: 2px 2px 0 0;
  background: #36b55d;
}
.mini-bars i:nth-child(3n) { background: #75db75; }
.pass-ring {
  --rate: 0deg;
  width: 72px;
  height: 72px;
  flex: 0 0 auto;
  padding: 9px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: conic-gradient(#6558e8 0 var(--rate), #12aaf2 var(--rate), #dcd9fa 0);
}
.pass-ring span {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #f3f1ff;
}
@media (max-width: 1100px) {
  .overview-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .overview-panel { padding: 12px; }
  .overview-grid { grid-template-columns: 1fr; }
  .overview-tile { min-height: 122px; }
}

.section-card {
  padding: var(--app-space-5);
  border-radius: 2px;
}
.section-title {
  font-size: 15px;
  font-weight: 650;
  color: var(--color-text-1);
  margin: 0;
}
.section-subtitle {
  font-size: 12px;
  color: var(--color-text-3);
  margin: 2px 0 0 0;
}
/* 成绩检索台账：以审计台账式筛选轨道承接多维检索 */
.score-ledger {
  padding: 0;
  overflow: hidden;
  border-top: 3px solid #234e70;
}
.ledger-heading {
  padding: 20px 22px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}
.ledger-eyebrow {
  margin-bottom: 7px;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #2f6f9f;
  font-size: 11px;
  font-weight: 750;
  letter-spacing: .08em;
}
.ledger-title { font-size: 16px; }
.filter-rail {
  padding: 15px 22px;
  display: grid;
  grid-template-columns: minmax(210px, 1.45fr) minmax(140px, .85fr) minmax(140px, .8fr) minmax(170px, 1fr);
  gap: 12px 14px;
  background: #f3f7fa;
  border-top: 1px solid #e2eaf0;
  border-bottom: 1px solid #e2eaf0;
}
.filter-field {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.filter-field label {
  color: #5c6f82;
  font-size: 11px;
  font-weight: 650;
}
.filter-field :deep(.arco-select),
.filter-field :deep(.arco-picker) { width: 100%; }
.date-filter-field { grid-column: span 2; }
.range-inputs { display: flex; align-items: center; gap: 6px; color: #93a3b3; }
.range-inputs :deep(.arco-input-number) { width: calc(50% - 10px); }
.filter-actions {
  display: flex;
  align-items: flex-end;
  gap: 8px;
}
.ledger-summary {
  min-height: 60px;
  padding: 10px 22px;
  display: flex;
  align-items: center;
  gap: 0;
  border-bottom: 1px solid #edf1f5;
  background: #fff;
}
.ledger-summary > div {
  min-width: 120px;
  padding: 2px 20px;
  display: flex;
  align-items: baseline;
  gap: 8px;
  border-right: 1px solid #e7edf2;
}
.ledger-summary > div:first-child { padding-left: 0; }
.ledger-summary > div:last-child { border-right: 0; }
.ledger-summary span { color: #8291a2; font-size: 11px; }
.ledger-summary strong { color: #26384b; font-size: 19px; font-variant-numeric: tabular-nums; }
.ledger-summary .summary-amber { color: #b7791f; }
.ledger-summary .summary-green { color: #14805e; }
.ledger-summary .summary-blue { color: #276a9b; }
.score-ledger :deep(.arco-table-container) { margin: 0 12px; }
.student-cell,
.score-cell { display: flex; flex-direction: column; gap: 2px; }
.student-cell strong { color: #23364b; font-size: 13px; }
.student-cell span,
.score-cell span { color: #91a0b1; font-size: 10px; }
.score-cell strong { color: #246a9b; font-size: 14px; }
.score-cell.is-pending strong { color: #b7791f; font-size: 12px; }
.mono-cell { color: #4d6075; font-family: Consolas, monospace; font-size: 11px; }
.date-cell { color: #8190a1; font-size: 11px; }
.ledger-pagination {
  padding: 14px 20px 17px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #8291a2;
  font-size: 11px;
  border-top: 1px solid #edf1f5;
}
@media (max-width: 1080px) {
  .filter-rail { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .date-filter-field { grid-column: span 1; }
}
@media (max-width: 680px) {
  .filter-group { width: 100%; align-items: stretch; flex-direction: column; gap: 5px; }
  .exam-select-box { width: 100%; }
  .ledger-heading { flex-direction: column; }
  .filter-rail { grid-template-columns: 1fr; }
  .ledger-summary { overflow-x: auto; }
  .filter-actions { align-items: center; }
  .ledger-pagination { align-items: flex-start; gap: 10px; flex-direction: column; }
}

</style>
