<template>
  <AppPage class="grading-page">
    <AppPageHeader
      eyebrow="考试运营"
      title="阅卷工作台"
      description="集中处理主观题评分、复核与整卷查看"
    />
    <AppPanel title="主观题阅卷列表" :description="`共 ${items.length} 份答卷 / 待批阅 ${pendingCount} 份`" flush>
      <AppToolbar>
        <div class="toolbar-filters">
          <!-- 考试任务筛选 -->
          <div class="exam-select">
            <a-select
              v-model="filterExamId"
              placeholder="全部考试任务"
              allow-clear
              @change="fetchItems"
            >
              <a-option
                v-for="task in examTasks"
                :key="task.id"
                :label="task.title"
                :value="task.id"
              />
            </a-select>
          </div>

          <!-- 批阅状态筛选 -->
          <div class="status-select">
            <a-select
              v-model="filterStatus"
              placeholder="批阅状态"
              @change="fetchItems"
            >
              <a-option label="全部答卷" value="all" />
              <a-option label="待批阅" value="pending" />
              <a-option label="已出分" value="graded" />
            </a-select>
          </div>

          <!-- 搜索框 -->
          <a-input
            v-model="searchKeyword" 
            placeholder="搜索学员姓名或题干" 
            allow-clear
            class="search-input"
            @keyup.enter="fetchItems"
            @clear="fetchItems"
          >
            <template #prefix><icon-search /></template>
          </a-input>

        </div>
        <template #actions>
          <div class="action-btn-group">
            <a-button @click="fetchItems">
              <template #icon><icon-refresh /></template>刷新数据
            </a-button>
            <a-button
              type="primary" 
              class="pipeline-btn" 
              :disabled="pendingCount === 0"
              @click="openPipelineMode"
            >
              流水盲阅模式 ({{ pendingCount }})
            </a-button>
          </div>
        </template>
      </AppToolbar>

      <!-- 主观题数据表格 -->
      <div class="table-wrapper">
        <a-table
          :columns="gradingColumns"
          :data="items"
          :loading="loading"
          :pagination="false"
          row-key="detail_id"
          class="custom-data-table"
        >
          <template #candidate="{ record }">
              <div class="candidate-row">
                <span class="candidate-name">{{ record.student_name }}</span>
                <span class="candidate-dept">{{ record.department_name }}</span>
              </div>
          </template>
          <template #question="{ record }"><span class="question-text">{{ record.question_title }}</span></template>
          <template #answer="{ record }"><span class="answer-preview">{{ answerSummary(record.user_answer) }}</span></template>
          <template #score="{ record }">
              <span v-if="record.is_graded" class="score-graded">
                {{ record.actual_score }} / {{ record.max_score }}分
              </span>
              <span v-else class="score-pending">
                待评 / {{ record.max_score }}分
              </span>
          </template>
          <template #status="{ record }">
              <span class="status-pill" :class="record.is_graded ? 'pill-graded' : 'pill-pending'">
                {{ record.is_graded ? '已评阅' : '待批阅' }}
              </span>
          </template>
          <template #operations="{ record }">
              <div class="table-ops">
                <a-button type="text" size="mini" @click="openGradingDrawer(record)">
                  {{ record.is_graded ? '复核打分' : '即时评分' }}
                </a-button>
                <a-button type="text" size="mini" @click="viewFullPaper(record)">查看整卷</a-button>
              </div>
          </template>
        </a-table>
      </div>

      <!-- 底部统计 -->
      <template #footer>
        <span class="footer-total">共 {{ items.length }} 条主观题作答记录</span>
      </template>
    </AppPanel>

    <!-- 指定查看与打分抽屉 -->
    <a-drawer
      v-model:visible="drawerVisible"
      :title="activeDetail?.is_graded ? '复核主观题评分' : '主观题即时打分'" 
      width="640px"
      unmount-on-close
      :footer="false"
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
            <div class="answer-document text-sm text-slate-800 bg-blue-50/30 p-3.5 rounded border border-blue-100 leading-relaxed">
              <MarkdownAnswer :answer="activeDetail.user_answer" empty-text="（考生未填写任何内容）" />
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
            <a-form layout="vertical">
              <a-form-item label="给予得分" required>
                <div class="flex items-center gap-3">
                  <a-input-number
                    v-model="drawerForm.score" 
                    :min="0" 
                    :max="activeDetail.max_score" 
                    size="default" 
                  />
                  <span class="text-slate-400 text-xs">/ 满分 {{ activeDetail.max_score }} 分</span>
                </div>
              </a-form-item>

              <a-form-item label="考官阅卷评语">
                <a-textarea
                  v-model="drawerForm.comment" 
                  :rows="3" 
                  placeholder="写明回答亮点或扣分理由..." 
                />
              </a-form-item>
            </a-form>
          </div>
        </div>

        <div class="pt-4 border-t border-slate-100 flex justify-end gap-3 mt-4">
          <a-button @click="drawerVisible = false">取消</a-button>
          <a-button type="primary" :loading="drawerSaving" @click="saveDrawerGrade">
            确认保存得分
          </a-button>
        </div>
      </div>
    </a-drawer>

    <!-- 流水盲阅弹窗模式 -->
    <a-modal v-model:visible="pipelineDialogVisible" title="沉浸式流水线阅卷" width="840px" unmount-on-close>
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
          <div class="answer-document p-3 bg-blue-50/30 rounded border border-blue-100 text-sm text-slate-800">
            <MarkdownAnswer :answer="currentPipelineItem.user_answer" empty-text="（未填写内容）" />
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
            <a-input-number v-model="pipelineScore" :min="0" :max="currentPipelineItem.max_score" size="small" />
            <span class="text-xs text-slate-400">/ {{ currentPipelineItem.max_score }} 分</span>
          </div>
          <a-textarea v-model="pipelineComment" :rows="2" placeholder="评语说明 (选填)..." />
        </div>
      </div>

      <template #footer>
        <div class="flex justify-between items-center w-full">
          <a-button :disabled="currentPipelineIndex === 0" @click="prevPipelineItem">上一题</a-button>
          <div class="flex gap-2">
            <a-button @click="pipelineDialogVisible = false">退出流水线</a-button>
            <a-button type="primary" :loading="pipelineSaving" @click="submitPipelineGrade">保存并批阅下一题</a-button>
          </div>
        </div>
      </template>
    </a-modal>
  </AppPage>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { gradingApi, examApi } from '@/api'
import { Message } from '@arco-design/web-vue'
import MarkdownAnswer from '@/components/exam/MarkdownAnswer.vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppToolbar from '@/components/ui/AppToolbar.vue'

const router = useRouter()

const loading = ref(false)
const items = ref([])
const examTasks = ref([])
const filterExamId = ref(null)
const filterStatus = ref('all')
const searchKeyword = ref('')
const gradingColumns = [
  { title: 'ID', dataIndex: 'detail_id', width: 70, align: 'center' },
  { title: '考生姓名', minWidth: 160, slotName: 'candidate' },
  { title: '所属考试', dataIndex: 'exam_title', minWidth: 200, ellipsis: true, tooltip: true },
  { title: '主观题干', dataIndex: 'question_title', minWidth: 260, ellipsis: true, tooltip: true, slotName: 'question' },
  { title: '考生作答摘要', minWidth: 240, ellipsis: true, tooltip: true, slotName: 'answer' },
  { title: '得分 / 满分', width: 120, align: 'center', slotName: 'score' },
  { title: '状态', width: 100, align: 'center', slotName: 'status' },
  { title: '操作', width: 180, align: 'center', fixed: 'right', slotName: 'operations' },
]

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

const answerSummary = (answer) => {
  if (typeof answer === 'string') return answer.trim() || '(考生未作答)'
  const content = String(answer?.content || '').replace(/!\[[^\]]*\]\(attachment:\d+\)/g, '[图片]').trim()
  if (content) return content
  return answer?.attachments?.length ? `[${answer.attachments.length} 张图片]` : '(考生未作答)'
}

const viewFullPaper = (row) => {
  router.push({ path: `/exam/result/${row.record_id}`, query: { from: 'grading' } })
}

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
    Message.success('主观题评分成功！')
    drawerVisible.value = false
    fetchItems()
  } finally {
    drawerSaving.value = false
  }
}

// 流水盲阅
const openPipelineMode = () => {
  if (pendingItemsList.value.length === 0) {
    Message.info('暂无待批阅的主观题')
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
    Message.success('评分已保存！')
    await fetchItems()
    if (currentPipelineIndex.value >= pendingItemsList.value.length) {
      pipelineDialogVisible.value = false
      Message.success('恭喜！所有待批阅主观题均已批阅完成！')
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
  --app-page-gap: var(--app-space-4);
}

.toolbar-filters {
  display: flex;
  align-items: center;
  gap: var(--app-space-2);
  flex-wrap: wrap;
}

.exam-select {
  width: 180px;
  flex: 0 0 180px;
}
.exam-select :deep(.arco-select),
.status-select :deep(.arco-select) { width: 100%; }
.status-select {
  width: 120px;
  flex: 0 0 120px;
}
.search-input {
  width: 210px;
  flex: 0 0 210px;
}

.action-btn-group {
  flex: 0 0 auto;
  display: flex;
  gap: 8px;
  align-items: center;
}

@media (max-width: 760px) {
  .exam-select { width: min(100%, 210px); flex: 1 1 180px; }
  .status-select { width: 120px; flex-basis: 120px; }
  .search-input { width: min(100%, 210px); flex: 1 1 180px; }
}
.pipeline-btn {
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
  border-radius: var(--app-radius-control);
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

.footer-total {
  font-size: 12px;
  color: #64748b;
}
</style>
