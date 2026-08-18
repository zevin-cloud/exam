<template>
  <div class="grading-page">
    <!-- 一体化专业卡片 (参照题库与试题管理设计) -->
    <div class="grading-card app-card">
      <!-- 顶部工具栏 -->
      <div class="card-toolbar">
        <div class="toolbar-left">
          <h3 class="card-title">主观题阅卷列表</h3>
          <span class="count-badge">共 {{ items.length }} 份答卷 / 待批阅 {{ pendingCount }} 份</span>
        </div>

        <div class="toolbar-right">
          <!-- 考试任务筛选 -->
          <el-select 
            v-model="filterExamId" 
            placeholder="全部考试任务" 
            clearable 
            class="exam-select"
            @change="fetchItems"
          >
            <el-option 
              v-for="task in examTasks" 
              :key="task.id" 
              :label="task.title" 
              :value="task.id" 
            />
          </el-select>

          <!-- 批阅状态筛选 -->
          <el-select 
            v-model="filterStatus" 
            placeholder="批阅状态" 
            class="status-select"
            @change="fetchItems"
          >
            <el-option label="全部答卷" value="all" />
            <el-option label="待批阅" value="pending" />
            <el-option label="已出分" value="graded" />
          </el-select>

          <!-- 搜索框 -->
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索学员姓名或题干" 
            clearable 
            class="search-input"
            @keyup.enter="fetchItems"
            @clear="fetchItems"
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
            <el-button @click="fetchItems">
              刷新数据
            </el-button>
            <el-button 
              type="primary" 
              class="pipeline-btn" 
              :disabled="pendingCount === 0"
              @click="openPipelineMode"
            >
              流水盲阅模式 ({{ pendingCount }})
            </el-button>
          </div>
        </div>
      </div>

      <!-- 主观题数据表格 -->
      <div class="table-wrapper">
        <el-table 
          :data="items" 
          v-loading="loading" 
          style="width: 100%"
          class="custom-data-table"
        >
          <el-table-column prop="detail_id" label="ID" width="70" align="center" />
          
          <el-table-column label="考生姓名" min-width="160">
            <template #default="{ row }">
              <div class="candidate-row">
                <span class="candidate-name">{{ row.student_name }}</span>
                <span class="candidate-dept">{{ row.department_name }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="exam_title" label="所属考试" min-width="200" show-overflow-tooltip />

          <el-table-column prop="question_title" label="主观题干" min-width="260" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="question-text">{{ row.question_title }}</span>
            </template>
          </el-table-column>

          <el-table-column label="考生作答摘要" min-width="240" show-overflow-tooltip>
            <template #default="{ row }">
              <span class="answer-preview">{{ row.user_answer || '(考生未作答)' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="得分 / 满分" width="120" align="center">
            <template #default="{ row }">
              <span v-if="row.is_graded" class="score-graded">
                {{ row.actual_score }} / {{ row.max_score }}分
              </span>
              <span v-else class="score-pending">
                待评 / {{ row.max_score }}分
              </span>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <span class="status-pill" :class="row.is_graded ? 'pill-graded' : 'pill-pending'">
                {{ row.is_graded ? '已评阅' : '待批阅' }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="130" align="center" fixed="right">
            <template #default="{ row }">
              <div class="table-ops">
                <el-button link type="primary" size="small" @click="openGradingDrawer(row)">
                  {{ row.is_graded ? '复核打分' : '即时评分' }}
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 底部统计 -->
      <div class="card-footer">
        <span class="footer-total">共 {{ items.length }} 条主观题作答记录</span>
      </div>
    </div>

    <!-- 指定查看与打分抽屉 -->
    <el-drawer 
      v-model="drawerVisible" 
      :title="activeDetail?.is_graded ? '复核主观题评分' : '主观题即时打分'" 
      size="560px"
      destroy-on-close
    >
      <div v-if="activeDetail" class="drawer-content flex flex-col justify-between h-full">
        <div>
          <!-- 考生与题目元信息 -->
          <div class="p-3.5 bg-slate-50 rounded-lg border border-slate-200 mb-4">
            <div class="flex justify-between items-center mb-1.5">
              <span class="font-bold text-slate-800 text-sm">{{ activeDetail.student_name }}</span>
              <span class="status-pill" :class="activeDetail.is_graded ? 'pill-graded' : 'pill-pending'">
                {{ activeDetail.is_graded ? `已评 ${activeDetail.actual_score}分` : '待评分' }}
              </span>
            </div>
            <div class="text-xs text-slate-500">
              <div>所属部门: {{ activeDetail.department_name }} | 邮箱: {{ activeDetail.student_email || '-' }}</div>
              <div class="mt-1">所属考试: {{ activeDetail.exam_title }}</div>
            </div>
          </div>

          <!-- 题干 -->
          <div class="mb-4">
            <div class="text-xs font-bold text-slate-500 mb-1">主观题目 (满分 {{ activeDetail.max_score }} 分)：</div>
            <div class="text-sm font-semibold text-slate-800 bg-slate-50 p-3 rounded border border-slate-100 leading-relaxed">
              {{ activeDetail.question_title }}
            </div>
          </div>

          <!-- 考生作答 -->
          <div class="mb-4">
            <div class="text-xs font-bold text-slate-500 mb-1">考生作答内容：</div>
            <div class="text-sm text-slate-800 bg-blue-50/30 p-3.5 rounded border border-blue-100 font-mono whitespace-pre-wrap leading-relaxed">
              {{ activeDetail.user_answer || '(考生未填写任何文字)' }}
            </div>
          </div>

          <!-- 标准参考采分点 -->
          <div class="mb-4">
            <div class="text-xs font-bold text-green-800 mb-1">参考采分点与评分标准：</div>
            <div class="text-xs text-green-800 bg-green-50/60 p-3 rounded border border-green-200 leading-relaxed">
              {{ activeDetail.reference_answer }}
            </div>
          </div>

          <!-- 打分与评语表单 -->
          <div class="p-4 bg-white rounded-lg border border-slate-200">
            <el-form label-position="top">
              <el-form-item label="给予得分" required>
                <div class="flex items-center gap-3">
                  <el-input-number 
                    v-model="drawerForm.score" 
                    :min="0" 
                    :max="activeDetail.max_score" 
                    size="default" 
                  />
                  <span class="text-slate-400 text-xs">/ 满分 {{ activeDetail.max_score }} 分</span>
                </div>
              </el-form-item>

              <el-form-item label="考官阅卷评语">
                <el-input 
                  v-model="drawerForm.comment" 
                  type="textarea" 
                  :rows="3" 
                  placeholder="写明回答亮点或扣分理由..." 
                />
              </el-form-item>
            </el-form>
          </div>
        </div>

        <div class="pt-4 border-t border-slate-100 flex justify-end gap-3 mt-4">
          <el-button @click="drawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="drawerSaving" @click="saveDrawerGrade">
            确认保存得分
          </el-button>
        </div>
      </div>
    </el-drawer>

    <!-- 流水盲阅弹窗模式 -->
    <el-dialog v-model="pipelineDialogVisible" title="沉浸式流水流水线阅卷" width="780px" destroy-on-close>
      <div v-if="currentPipelineItem" class="pipeline-wrap">
        <div class="flex justify-between items-center mb-3 text-xs text-slate-500">
          <span>所属考试: <strong>{{ currentPipelineItem.exam_title }}</strong></span>
          <span>进度: <strong>{{ currentPipelineIndex + 1 }}</strong> / {{ pendingItemsList.length }} 题</span>
        </div>

        <div class="p-3 bg-slate-50 rounded border border-slate-100 mb-3">
          <div class="text-xs text-slate-400 mb-1">题目题干 (满分 {{ currentPipelineItem.max_score }} 分)：</div>
          <div class="font-bold text-slate-800 text-sm leading-relaxed">{{ currentPipelineItem.question_title }}</div>
        </div>

        <div class="mb-3">
          <div class="text-xs font-bold text-slate-500 mb-1">考生作答内容：</div>
          <div class="p-3 bg-blue-50/30 rounded border border-blue-100 font-mono text-sm text-slate-800 whitespace-pre-wrap">
            {{ currentPipelineItem.user_answer || '(未填写内容)' }}
          </div>
        </div>

        <div class="mb-4">
          <div class="text-xs font-bold text-green-800 mb-1">参考采分点：</div>
          <div class="p-2.5 bg-green-50 rounded border border-green-200 text-xs text-green-800">
            {{ currentPipelineItem.reference_answer }}
          </div>
        </div>

        <div class="p-3 bg-slate-50 rounded border border-slate-200">
          <div class="flex items-center gap-3 mb-2">
            <span class="text-xs font-bold text-slate-700">给予得分:</span>
            <el-input-number v-model="pipelineScore" :min="0" :max="currentPipelineItem.max_score" size="small" />
            <span class="text-xs text-slate-400">/ {{ currentPipelineItem.max_score }} 分</span>
          </div>
          <el-input v-model="pipelineComment" type="textarea" :rows="2" placeholder="评语说明 (选填)..." />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-between items-center w-full">
          <el-button :disabled="currentPipelineIndex === 0" @click="prevPipelineItem">上一题</el-button>
          <div class="flex gap-2">
            <el-button @click="pipelineDialogVisible = false">退出流水线</el-button>
            <el-button type="primary" :loading="pipelineSaving" @click="submitPipelineGrade">保存并批阅下一题</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { gradingApi, examApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const items = ref([])
const examTasks = ref([])
const filterExamId = ref(null)
const filterStatus = ref('all')
const searchKeyword = ref('')

// 抽屉指定查看
const drawerVisible = ref(false)
const drawerSaving = ref(false)
const activeDetail = ref(null)
const drawerForm = ref({
  score: 0,
  comment: ''
})

// 流水盲阅弹窗
const pipelineDialogVisible = ref(false)
const pipelineSaving = ref(false)
const currentPipelineIndex = ref(0)
const pipelineScore = ref(0)
const pipelineComment = ref('')

const pendingItemsList = computed(() => {
  return items.value.filter(i => !i.is_graded)
})

const pendingCount = computed(() => {
  return items.value.filter(i => !i.is_graded).length
})

const currentPipelineItem = computed(() => {
  return pendingItemsList.value[currentPipelineIndex.value] || null
})

const fetchExamTasks = async () => {
  try {
    const res = await examApi.getTasks()
    examTasks.value = res
  } catch (e) {
    //
  }
}

const fetchItems = async () => {
  loading.value = true
  try {
    const params = {}
    if (filterExamId.value) params.exam_task_id = filterExamId.value
    if (filterStatus.value) params.status = filterStatus.value
    if (searchKeyword.value) params.keyword = searchKeyword.value

    const res = await gradingApi.getPendingItems(params)
    items.value = res
  } finally {
    loading.value = false
  }
}

// 抽屉指定查看与评分
const openGradingDrawer = (row) => {
  activeDetail.value = row
  drawerForm.value = {
    score: row.is_graded ? row.actual_score : row.max_score,
    comment: row.teacher_comment || ''
  }
  drawerVisible.value = true
}

const saveDrawerGrade = async () => {
  drawerSaving.value = true
  try {
    await gradingApi.gradeItem({
      detail_id: activeDetail.value.detail_id,
      score: drawerForm.value.score,
      comment: drawerForm.value.comment
    })
    ElMessage.success('主观题评分成功！')
    drawerVisible.value = false
    fetchItems()
  } finally {
    drawerSaving.value = false
  }
}

// 流水盲阅
const openPipelineMode = () => {
  if (pendingItemsList.value.length === 0) {
    ElMessage.info('暂无待批阅的主观题')
    return
  }
  currentPipelineIndex.value = 0
  syncPipelineForm()
  pipelineDialogVisible.value = true
}

const syncPipelineForm = () => {
  if (currentPipelineItem.value) {
    pipelineScore.value = currentPipelineItem.value.max_score
    pipelineComment.value = ''
  }
}

const prevPipelineItem = () => {
  if (currentPipelineIndex.value > 0) {
    currentPipelineIndex.value--
    syncPipelineForm()
  }
}

const submitPipelineGrade = async () => {
  if (!currentPipelineItem.value) return
  pipelineSaving.value = true
  try {
    await gradingApi.gradeItem({
      detail_id: currentPipelineItem.value.detail_id,
      score: pipelineScore.value,
      comment: pipelineComment.value
    })
    ElMessage.success('评分已保存！')
    await fetchItems()
    if (currentPipelineIndex.value >= pendingItemsList.value.length) {
      pipelineDialogVisible.value = false
      ElMessage.success('恭喜！所有待批阅主观题均已批阅完成！')
    } else {
      syncPipelineForm()
    }
  } finally {
    pipelineSaving.value = false
  }
}

onMounted(() => {
  fetchExamTasks()
  fetchItems()
})
</script>

<style scoped>
.grading-page {
  max-width: 1360px;
  margin: 0 auto;
}

/* 主体卡片 (与题库管理完全一致) */
.grading-card {
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

.exam-select {
  width: 180px;
}
.status-select {
  width: 110px;
}
.search-input {
  width: 200px;
}

.action-btn-group {
  display: flex;
  gap: 8px;
  align-items: center;
}
.pipeline-btn {
  border-radius: 6px;
  font-weight: 600;
}

/* 表格字段样式 */
.candidate-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.candidate-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 13.5px;
}
.candidate-dept {
  font-size: 11px;
  color: #94a3b8;
}

.question-text {
  font-weight: 500;
  color: #334155;
  font-size: 13px;
}

.answer-preview {
  font-size: 12.5px;
  color: #64748b;
  font-family: monospace;
}

.score-graded {
  font-weight: 700;
  color: #059669;
  font-size: 13px;
}
.score-pending {
  color: #94a3b8;
  font-size: 12px;
}

/* 状态胶囊 */
.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.pill-graded { background: #ecfdf5; color: #059669; }
.pill-pending { background: #fffbeb; color: #d97706; }

.table-ops {
  display: flex;
  align-items: center;
  justify-content: center;
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
