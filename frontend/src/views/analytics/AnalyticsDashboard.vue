<template>
  <div class="analytics-container">
    <!-- 顶部标题与场次筛选控制栏 -->
    <div class="page-header app-card">
      <div class="header-left">
        <div class="header-icon-box">
          <BarChart3 :size="20" class="text-blue-600" />
        </div>
        <div>
          <h2 class="header-title">考务分析与知识盲区大盘</h2>
          <p class="header-desc">支持按场次穿透分析：部门及格率、失分盲区排行、成绩分布与全员总榜</p>
        </div>
      </div>

      <div class="header-right">
        <!-- 考试场次筛选器 -->
        <div class="filter-group">
          <span class="filter-label">统计场次:</span>
          <el-select 
            v-model="selectedExamId" 
            placeholder="全量考务综合汇总" 
            class="exam-select-box"
            @change="handleExamChange"
          >
            <el-option :value="null" label="全量考务综合汇总 (All Exams)" />
            <el-option 
              v-for="task in examTasks" 
              :key="task.id" 
              :label="`#${task.id} ${task.title}`" 
              :value="task.id" 
            />
          </el-select>
        </div>

        <el-button type="primary" plain @click="refreshAll" :loading="loading">
          刷新大盘
        </el-button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="32" color="#3b82f6"><Loading /></el-icon>
      <p class="loading-text">正在汇总分析考务数据...</p>
    </div>

    <template v-else-if="dashboardData">
      <!-- 4 大核心 KPI 指标卡片 -->
      <div class="kpi-grid">
        <!-- 实考人次 -->
        <div class="kpi-card app-card">
          <div class="kpi-body">
            <div class="kpi-title">累计实考人次</div>
            <div class="kpi-value text-slate-800">
              {{ dashboardData.overview.total_takers }} <span class="kpi-unit">人次</span>
            </div>
            <div class="kpi-footer">
              应考: {{ dashboardData.overview.total_eligible }} 人 | 缺考: <span class="text-rose-500 font-semibold">{{ dashboardData.overview.total_absent }}</span> 人
            </div>
          </div>
          <div class="kpi-icon-wrap icon-blue">
            <Users :size="22" />
          </div>
        </div>

        <!-- 综合及格率 -->
        <div class="kpi-card app-card">
          <div class="kpi-body">
            <div class="kpi-title">综合通过及格率</div>
            <div class="kpi-value text-emerald-600">
              {{ dashboardData.overview.pass_rate }}%
            </div>
            <div class="kpi-footer">
              <span class="status-dot" :class="dashboardData.overview.pass_rate >= 60 ? 'dot-success' : 'dot-warn'"></span>
              {{ dashboardData.overview.pass_rate >= 80 ? '考核达标优秀' : (dashboardData.overview.pass_rate >= 60 ? '考核及格达标' : '需重点组织复训') }}
            </div>
          </div>
          <div class="kpi-icon-wrap icon-emerald">
            <Target :size="22" />
          </div>
        </div>

        <!-- 场次平均得分 -->
        <div class="kpi-card app-card">
          <div class="kpi-body">
            <div class="kpi-title">全员平均得分</div>
            <div class="kpi-value text-indigo-600">
              {{ dashboardData.overview.avg_score }} <span class="kpi-unit">分</span>
            </div>
            <div class="kpi-footer">
              最高: <strong>{{ dashboardData.overview.max_score }}</strong> 分 | 最低: <strong>{{ dashboardData.overview.min_score }}</strong> 分
            </div>
          </div>
          <div class="kpi-icon-wrap icon-indigo">
            <TrendingUp :size="22" />
          </div>
        </div>

        <!-- 涵盖知识维度 -->
        <div class="kpi-card app-card">
          <div class="kpi-body">
            <div class="kpi-title">涵盖知识模块</div>
            <div class="kpi-value text-amber-600">
              {{ dashboardData.knowledge_radar?.length || 0 }} <span class="kpi-unit">个模块</span>
            </div>
            <div class="kpi-footer">
              高频错题归集: {{ dashboardData.wrong_top_questions?.length || 0 }} 题
            </div>
          </div>
          <div class="kpi-icon-wrap icon-amber">
            <BookOpen :size="22" />
          </div>
        </div>
      </div>

      <!-- 第二行：各部门考核表现横向排行 + 成绩分布区间结构 -->
      <div class="two-col-grid">
        <!-- 部门表现分析 -->
        <div class="app-card section-card">
          <div class="section-header">
            <div>
              <h3 class="section-title">各部门考核通过率与表现对比</h3>
              <p class="section-subtitle">按部门及格率排序，辅助横向识别部门学习成效</p>
            </div>
            <span class="badge-count">共 {{ dashboardData.dept_stats?.length || 0 }} 个部门</span>
          </div>

          <div v-if="!dashboardData.dept_stats?.length" class="empty-placeholder">
            暂无部门参考统计数据
          </div>

          <div v-else class="dept-rank-list">
            <div 
              v-for="(dept, idx) in dashboardData.dept_stats" 
              :key="dept.dept_name"
              class="dept-rank-row"
            >
              <div class="dept-info-line">
                <div class="dept-left">
                  <span class="rank-idx" :class="idx < 3 ? 'rank-top' : ''">{{ idx + 1 }}</span>
                  <span class="dept-name">{{ dept.dept_name }}</span>
                  <span class="dept-count">({{ dept.total_count }}人参考)</span>
                </div>
                <div class="dept-right">
                  <span class="dept-score">均分: {{ dept.avg_score }}分</span>
                  <span class="dept-pass-rate">及格率: {{ dept.pass_rate }}%</span>
                </div>
              </div>
              <el-progress 
                :percentage="dept.pass_rate" 
                :color="getProgressColor(dept.pass_rate)"
                :stroke-width="7" 
                :show-text="false"
              />
            </div>
          </div>
        </div>

        <!-- 成绩区间分布 -->
        <div class="app-card section-card flex-between-card">
          <div>
            <div class="section-header">
              <div>
                <h3 class="section-title">考生成绩区间与正态分布结构</h3>
                <p class="section-subtitle">全员分数阶梯分布，评估试卷区分度与难度适宜性</p>
              </div>
            </div>

            <div class="score-dist-list">
              <div 
                v-for="dist in dashboardData.score_distribution" 
                :key="dist.label"
                class="dist-card"
                :class="getDistBoxClass(dist.label)"
              >
                <div class="dist-card-header">
                  <span class="dist-label">{{ dist.label }}</span>
                  <div class="dist-count-group">
                    <span class="dist-count-num">{{ dist.count }} 人</span>
                    <span class="dist-percent">({{ dist.percentage }}%)</span>
                  </div>
                </div>
                <el-progress 
                  :percentage="dist.percentage" 
                  :color="getDistColor(dist.label)"
                  :stroke-width="6" 
                  :show-text="false"
                />
              </div>
            </div>
          </div>

          <div class="hint-box">
            💡 <strong>考务建议</strong>：若高分段过于集中，建议增加中高难度题目；若低分段占比过高，需对员工薄弱模块进行专项培训。
          </div>
        </div>
      </div>

      <!-- 第三行：失分盲区高频错题 Top 排行 + 知识模块掌握度 -->
      <div class="two-col-grid">
        <!-- 错题排行榜 -->
        <div class="app-card section-card">
          <div class="section-header">
            <div>
              <h3 class="section-title">高频易错题目与知识盲区 Top 排行</h3>
              <p class="section-subtitle">错误率最高题目排行榜，快速定位全员共性知识弱项</p>
            </div>
          </div>

          <div v-if="!dashboardData.wrong_top_questions?.length" class="empty-placeholder">
            太棒了！暂无高频错题数据
          </div>

          <div v-else class="wrong-questions-list">
            <div 
              v-for="(q, idx) in dashboardData.wrong_top_questions" 
              :key="q.question_title"
              class="wrong-q-item"
            >
              <div class="wrong-q-top">
                <div class="wrong-q-title-wrap">
                  <span class="rank-idx" :class="idx < 3 ? 'rank-top-danger' : ''">{{ idx + 1 }}</span>
                  <span class="wrong-q-title">{{ q.question_title }}</span>
                </div>
                <span class="wrong-q-rate">错题率: {{ q.error_rate }}%</span>
              </div>
              <div class="wrong-q-meta">
                <span>所属知识点: <strong class="meta-tag">{{ q.knowledge_tag }}</strong></span>
                <span>作答 {{ q.total_attempts }} 次 / 答错 {{ q.wrong_count }} 次</span>
              </div>
              <el-progress 
                :percentage="q.error_rate" 
                color="#f43f5e" 
                :stroke-width="5" 
                :show-text="false" 
              />
            </div>
          </div>
        </div>

        <!-- 知识维度掌握度 -->
        <div class="app-card section-card">
          <div class="section-header">
            <div>
              <h3 class="section-title">企业业务技能与知识点掌握度透视</h3>
              <p class="section-subtitle">按业务标签聚合分析全员对不同技术与规章的掌握情况</p>
            </div>
          </div>

          <div v-if="!dashboardData.knowledge_radar?.length" class="empty-placeholder">
            暂无知识点标签分析数据
          </div>

          <div v-else class="radar-tag-list">
            <div 
              v-for="k in dashboardData.knowledge_radar" 
              :key="k.tag"
              class="radar-tag-item"
            >
              <div class="radar-tag-line">
                <span class="tag-title">{{ k.tag }}</span>
                <div class="tag-meta">
                  <span class="tag-attempt">考察 {{ k.total_count }} 题次</span>
                  <span class="tag-mastery" :class="k.mastery_rate >= 70 ? 'text-emerald' : 'text-amber'">
                    掌握度: {{ k.mastery_rate }}%
                  </span>
                </div>
              </div>
              <el-progress 
                :percentage="k.mastery_rate" 
                :color="k.mastery_rate >= 80 ? '#10b981' : (k.mastery_rate >= 60 ? '#3b82f6' : '#f59e0b')"
                :stroke-width="6" 
                :show-text="false"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 第四行：可检索、可导出的成绩台账 -->
      <div class="app-card section-card score-ledger">
        <div class="ledger-heading">
          <div>
            <div class="ledger-eyebrow"><SlidersHorizontal :size="13" /> 成绩检索台账</div>
            <h3 class="section-title ledger-title">按人员、部门、成绩与时间交叉检索</h3>
            <p class="section-subtitle">只统计每位考生每场考试最后一次有效答卷，当前筛选条件会原样应用到 Excel 导出。</p>
          </div>
          <el-button type="primary" :loading="exporting" @click="exportScores">
            <Download :size="15" /> 导出当前结果
          </el-button>
        </div>

        <div class="filter-rail">
          <div class="filter-field filter-keyword">
            <label>考生 / 账号 / 考试</label>
            <el-input v-model="scoreFilters.keyword" clearable placeholder="输入姓名、账号或考试名称" @keyup.enter="searchScores" />
          </div>
          <div class="filter-field">
            <label>所属部门（含下级）</label>
            <el-select v-model="scoreFilters.department_id" clearable filterable placeholder="全部部门">
              <el-option v-for="dept in departments" :key="dept.id" :label="dept.name" :value="dept.id" />
            </el-select>
          </div>
          <div class="filter-field">
            <label>成绩状态</label>
            <el-select v-model="scoreFilters.result_status">
              <el-option label="全部有效答卷" value="all" />
              <el-option label="及格" value="passed" />
              <el-option label="未及格" value="failed" />
              <el-option label="主观题待阅卷" value="pending" />
            </el-select>
          </div>
          <div class="filter-field score-range-field">
            <label>分数区间</label>
            <div class="range-inputs">
              <el-input-number v-model="scoreFilters.score_min" :min="0" :max="999" :controls="false" placeholder="最低" />
              <span>—</span>
              <el-input-number v-model="scoreFilters.score_max" :min="0" :max="999" :controls="false" placeholder="最高" />
            </div>
          </div>
          <div class="filter-field date-filter-field">
            <label>交卷时间</label>
            <el-date-picker
              v-model="scoreFilters.date_range"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD HH:mm:ss"
              :default-time="dateDefaultTimes"
            />
          </div>
          <div class="filter-field">
            <label>排序方式</label>
            <el-select v-model="scoreFilters.sort_by">
              <el-option label="最近交卷" value="submit_desc" />
              <el-option label="成绩从高到低" value="score_desc" />
              <el-option label="成绩从低到高" value="score_asc" />
              <el-option label="用时最短" value="duration_asc" />
              <el-option label="用时最长" value="duration_desc" />
            </el-select>
          </div>
          <div class="filter-actions">
            <el-button type="primary" @click="searchScores"><Search :size="15" /> 查询成绩</el-button>
            <el-button @click="resetScoreFilters"><RotateCcw :size="14" /> 重置</el-button>
          </div>
        </div>

        <div class="ledger-summary">
          <div><span>命中答卷</span><strong>{{ scoreData.summary.matched_count }}</strong></div>
          <div><span>已出分</span><strong>{{ scoreData.summary.scored_count }}</strong></div>
          <div><span>待阅卷</span><strong class="summary-amber">{{ scoreData.summary.pending_count }}</strong></div>
          <div><span>及格人数</span><strong class="summary-green">{{ scoreData.summary.passed_count }}</strong></div>
          <div><span>筛选后均分</span><strong class="summary-blue">{{ scoreData.summary.avg_score }}</strong></div>
        </div>

        <el-table :data="scoreData.items" v-loading="scoreLoading" stripe style="width: 100%" size="small" empty-text="当前条件下没有成绩记录">
          <el-table-column label="考生" min-width="165" fixed="left">
            <template #default="{ row }">
              <div class="student-cell">
                <strong>{{ row.student_name }}</strong>
                <span>{{ row.username }} · 第 {{ row.attempt_no }} 次</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="department_name" label="所属部门" min-width="140" show-overflow-tooltip />
          <el-table-column prop="exam_title" label="考试场次" min-width="210" show-overflow-tooltip />
          <el-table-column label="成绩构成" width="160" align="center">
            <template #default="{ row }">
              <div v-if="row.status === 'GRADED'" class="score-cell">
                <strong>{{ row.total_score }} 分</strong>
                <span>客观 {{ row.objective_score }} / 主观 {{ row.subjective_score }}</span>
              </div>
              <div v-else class="score-cell is-pending">
                <strong>待出分</strong>
                <span>客观题暂计 {{ row.objective_score }} 分</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="结果" width="105" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.status !== 'GRADED'" type="warning" size="small">待阅卷</el-tag>
              <el-tag v-else :type="row.is_passed ? 'success' : 'danger'" size="small">
                {{ row.is_passed ? '及格' : '未及格' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="作答用时" width="110" align="center">
            <template #default="{ row }"><span class="mono-cell">{{ formatDuration(row.duration_seconds) }}</span></template>
          </el-table-column>
          <el-table-column label="切屏" width="72" align="center" prop="screen_switch_count" />
          <el-table-column label="交卷时间" min-width="170" align="center">
            <template #default="{ row }"><span class="date-cell">{{ formatDate(row.submit_time) }}</span></template>
          </el-table-column>
          <el-table-column label="操作" width="95" align="center" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="viewPaper(row)">查看整卷</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="ledger-pagination">
          <span>共 {{ scoreData.total }} 条</span>
          <el-pagination
            v-model:current-page="scorePage"
            v-model:page-size="scorePageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="scoreData.total"
            layout="sizes, prev, pager, next"
            @change="fetchScores"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { analyticsApi, examApi, userApi } from '@/api'
import { 
  BarChart3, Users, Target, TrendingUp, BookOpen,
  Download, RotateCcw, Search, SlidersHorizontal
} from 'lucide-vue-next'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

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
const dateDefaultTimes = [new Date(2000, 0, 1, 0, 0, 0), new Date(2000, 0, 1, 23, 59, 59)]
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
    ElMessage.warning('最低分不能高于最高分')
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
    ElMessage.success(`已导出 ${scoreData.value.summary.matched_count} 条成绩记录`)
  } finally {
    exporting.value = false
  }
}

const viewPaper = (row) => {
  router.push({ path: `/exam/result/${row.record_id}`, query: { from: 'analytics' } })
}

const getProgressColor = (rate) => {
  if (rate >= 80) return '#10b981'
  if (rate >= 60) return '#3b82f6'
  return '#f59e0b'
}

const getDistBoxClass = (label) => {
  if (label.includes('优秀')) return 'dist-box-emerald'
  if (label.includes('良好')) return 'dist-box-blue'
  if (label.includes('合格')) return 'dist-box-slate'
  return 'dist-box-rose'
}

const getDistColor = (label) => {
  if (label.includes('优秀')) return '#10b981'
  if (label.includes('良好')) return '#3b82f6'
  if (label.includes('合格')) return '#64748b'
  return '#f43f5e'
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
  max-width: 1360px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 顶部控制栏 */
.page-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: #eff6ff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.header-desc {
  font-size: 12px;
  color: #94a3b8;
  margin: 2px 0 0 0;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
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
}
.exam-select-box {
  width: 280px;
}

/* KPI 网格 */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
@media (max-width: 1024px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 640px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
}

.kpi-card {
  padding: 18px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.kpi-body {
  display: flex;
  flex-direction: column;
}
.kpi-title {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}
.kpi-value {
  font-size: 26px;
  font-weight: 800;
  line-height: 1.2;
  margin: 4px 0;
}
.kpi-unit {
  font-size: 13px;
  font-weight: 500;
  color: #94a3b8;
}
.kpi-footer {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.kpi-icon-wrap {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.icon-blue { background: #eff6ff; color: #2563eb; }
.icon-emerald { background: #ecfdf5; color: #059669; }
.icon-indigo { background: #eef2ff; color: #4f46e5; }
.icon-amber { background: #fffbeb; color: #d97706; }

/* 两栏网格 */
.two-col-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 900px) {
  .two-col-grid {
    grid-template-columns: 1fr;
  }
}

.section-card {
  padding: 20px;
}
.flex-between-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.section-subtitle {
  font-size: 12px;
  color: #94a3b8;
  margin: 2px 0 0 0;
}
.badge-count {
  font-size: 12px;
  color: #2563eb;
  font-weight: 600;
}

/* 部门排名 */
.dept-rank-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dept-rank-row {
  padding: 12px 14px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
}
.dept-info-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 12px;
}
.dept-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dept-name {
  font-weight: 700;
  color: #334155;
}
.dept-count {
  color: #94a3b8;
}
.dept-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.dept-score {
  font-weight: 600;
  color: #475569;
}
.dept-pass-rate {
  font-weight: 700;
  color: #059669;
}

/* 成绩分布 */
.score-dist-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dist-card {
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.dist-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}
.dist-label {
  font-weight: 700;
}
.dist-count-group {
  display: flex;
  align-items: center;
  gap: 6px;
}
.dist-count-num {
  font-weight: 700;
}
.dist-percent {
  opacity: 0.8;
}
.dist-box-emerald { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
.dist-box-blue { background: #eff6ff; border-color: #bfdbfe; color: #1e40af; }
.dist-box-slate { background: #f8fafc; border-color: #e2e8f0; color: #334155; }
.dist-box-rose { background: #fff1f2; border-color: #fecdd3; color: #9f1239; }

.hint-box {
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin-top: 16px;
}

/* 错题排行榜 */
.wrong-questions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.wrong-q-item {
  padding: 12px 14px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.wrong-q-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}
.wrong-q-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
  padding-right: 8px;
}
.wrong-q-title {
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.wrong-q-rate {
  font-weight: 700;
  color: #e11d48;
  white-space: nowrap;
}
.wrong-q-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #94a3b8;
}
.meta-tag {
  color: #475569;
}

/* 知识雷达 */
.radar-tag-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.radar-tag-item {
  padding: 12px 14px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
}
.radar-tag-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 12px;
}
.tag-title {
  font-weight: 700;
  color: #1e293b;
}
.tag-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tag-attempt {
  color: #94a3b8;
  font-size: 11px;
}
.tag-mastery {
  font-weight: 700;
}
.text-emerald { color: #059669; }
.text-amber { color: #d97706; }

/* 排名徽章 */
.rank-idx {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  background: #e2e8f0;
  color: #475569;
  flex-shrink: 0;
}
.rank-top {
  background: #dbeafe;
  color: #2563eb;
}
.rank-top-danger {
  background: #ffe4e6;
  color: #e11d48;
}

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
}
.dot-success { background: #10b981; }
.dot-warn { background: #f59e0b; }

.empty-placeholder {
  text-align: center;
  padding: 40px 0;
  color: #94a3b8;
  font-size: 12px;
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
.filter-field :deep(.el-select),
.filter-field :deep(.el-date-editor) { width: 100%; }
.date-filter-field { grid-column: span 2; }
.range-inputs { display: flex; align-items: center; gap: 6px; color: #93a3b3; }
.range-inputs :deep(.el-input-number) { width: calc(50% - 10px); }
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
.score-ledger :deep(.el-table) { padding: 0 12px; }
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
  .ledger-heading { flex-direction: column; }
  .filter-rail { grid-template-columns: 1fr; }
  .ledger-summary { overflow-x: auto; }
  .filter-actions { align-items: center; }
  .ledger-pagination { align-items: flex-start; gap: 10px; flex-direction: column; }
}

.loading-state {
  text-align: center;
  padding: 80px 0;
}
.loading-text {
  color: #94a3b8;
  margin-top: 8px;
  font-size: 13px;
}
</style>
