<template>
  <div class="paper-list-container">
    <div class="page-header">
      <div class="header-title-wrap flex items-center gap-3">
        <div class="header-icon-box w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center border border-blue-100">
          <FileText :size="20" class="text-blue-600" />
        </div>
        <div>
          <h2 class="text-xl font-bold text-slate-800">试卷管理与组卷中心</h2>
          <p class="text-xs text-slate-500 mt-1">支持可视化拖拽设计与题库一键组卷，灵活配置题型与分值规则</p>
        </div>
      </div>

      <div class="flex gap-3">
        <el-button type="success" plain @click="openQuickGenerateDialog">
          <Sparkles :size="14" class="mr-1" /> 从题库快速选题组卷
        </el-button>
        <el-button type="primary" @click="createEmptyPaper">
          <Plus :size="14" class="mr-1" /> 可视化创建试卷
        </el-button>
      </div>
    </div>

    <!-- 试卷卡片列表 -->
    <div v-if="loading" class="text-center py-20">
      <el-icon class="is-loading" :size="32" color="#3b82f6"><Loading /></el-icon>
      <p class="text-slate-400 mt-2 text-sm">正在加载试卷库...</p>
    </div>

    <div v-else-if="paperList.length === 0" class="empty-box app-card text-center py-16 mt-4">
      <ClipboardList :size="48" class="text-slate-300 mx-auto mb-2" />
      <p class="text-slate-500 font-medium">暂无试卷，快来创建第一份考核试卷吧！</p>
    </div>

    <div v-else class="paper-grid mt-6">
      <div v-for="paper in paperList" :key="paper.id" class="paper-card app-card">
        <div class="paper-card-header">
          <span class="category-badge">{{ paper.category || '默认考卷' }}</span>
          <span class="version-tag">标准考核卷</span>
        </div>

        <h3 class="paper-title">{{ paper.title }}</h3>
        <p class="paper-desc">{{ paper.description || '暂无说明描述' }}</p>

        <div class="paper-metrics">
          <div class="metric">
            <span class="label">试卷总分</span>
            <span class="val text-blue-600 font-bold">{{ paper.total_score }} 分</span>
          </div>
          <div class="metric">
            <span class="label">及格线</span>
            <span class="val text-green-600 font-bold">{{ paper.pass_score }} 分</span>
          </div>
          <div class="metric">
            <span class="label">建议用时</span>
            <span class="val">{{ paper.suggest_duration }} 分钟</span>
          </div>
          <div class="metric">
            <span class="label">题目总数</span>
            <span class="val">{{ countPaperElements(paper) }} 题</span>
          </div>
        </div>

        <div class="paper-actions">
          <el-button type="primary" plain class="flex-1" @click="editPaper(paper.id)">
            <PenTool :size="13" class="mr-1" /> 编辑设计试卷
          </el-button>
          <el-button type="danger" link @click="deletePaper(paper.id)">
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 从题库选题一键组卷弹窗 -->
    <el-dialog v-model="quickGenVisible" title="从题库快速选题组卷" width="760px">
      <div class="p-2">
        <el-form :model="quickForm" label-width="90px">
          <el-form-item label="试卷标题" required>
            <el-input v-model="quickForm.title" placeholder="例如：2026年企业新员工入职考试试卷" />
          </el-form-item>
          <div class="grid grid-cols-2 gap-4">
            <el-form-item label="建议用时">
              <el-input-number v-model="quickForm.suggest_duration" :min="5" :max="180" /> 分钟
            </el-form-item>
            <el-form-item label="及格分数线">
              <el-input-number v-model="quickForm.pass_score" :min="1" :max="1000" /> 分
            </el-form-item>
          </div>
        </el-form>

        <div class="text-xs text-slate-500 font-semibold mb-2 mt-4">勾选要加入试卷的题目：</div>
        <el-table 
          :data="allQuestions" 
          v-loading="questionsLoading" 
          max-height="300"
          @selection-change="handleSelectionChange"
          stripe
        >
          <el-table-column type="selection" width="45" align="center" />
          <el-table-column prop="id" label="ID" width="60" align="center" />
          <el-table-column prop="type" label="题型" width="90">
            <template #default="{ row }">{{ getTypeName(row.type) }}</template>
          </el-table-column>
          <el-table-column prop="title" label="题干" show-overflow-tooltip />
          <el-table-column prop="score" label="分值" width="70" align="center">
            <template #default="{ row }">{{ row.score }}分</template>
          </el-table-column>
        </el-table>
        <div class="text-right text-xs text-slate-500 mt-2">
          已勾选 <strong>{{ selectedQuestionIds.length }}</strong> 道题目，预估总分：<strong>{{ selectedTotalScore }}</strong> 分
        </div>
      </div>

      <template #footer>
        <el-button @click="quickGenVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="submitQuickGenerate">一键生成试卷</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { paperApi, questionApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { FileText, Sparkles, Plus, ClipboardList, PenTool } from 'lucide-vue-next'

const router = useRouter()
const loading = ref(false)
const paperList = ref([])

// 快速组卷
const quickGenVisible = ref(false)
const questionsLoading = ref(false)
const generating = ref(false)
const allQuestions = ref([])
const selectedQuestionIds = ref([])

const quickForm = ref({
  title: '',
  description: '',
  category: '综合测试',
  suggest_duration: 45,
  pass_score: 60
})

const fetchPapers = async () => {
  loading.value = true
  try {
    const res = await paperApi.getPapers()
    paperList.value = res
  } catch (e) {
    //
  } finally {
    loading.value = false
  }
}

const countPaperElements = (paper) => {
  let count = 0
  for (const p of paper.schema_data?.pages || []) {
    count += (p.elements || []).length
  }
  return count
}

const createEmptyPaper = () => {
  router.push('/admin/papers/editor')
}

const editPaper = (id) => {
  router.push(`/admin/papers/editor/${id}`)
}

const deletePaper = (id) => {
  ElMessageBox.confirm('确定要删除该试卷吗？若已有发布的考务关联将受影响。', '删除确认', {
    type: 'warning'
  }).then(async () => {
    await paperApi.deletePaper(id)
    ElMessage.success('试卷已删除')
    fetchPapers()
  })
}

// 快速组卷逻辑
const openQuickGenerateDialog = async () => {
  quickForm.value.title = `企业标准化业务考核试卷 (${new Date().toLocaleDateString()})`
  quickGenVisible.value = true
  questionsLoading.value = true
  try {
    allQuestions.value = await questionApi.getQuestions()
  } finally {
    questionsLoading.value = false
  }
}

const handleSelectionChange = (selection) => {
  selectedQuestionIds.value = selection.map(item => item.id)
}

const selectedTotalScore = computed(() => {
  const map = new Set(selectedQuestionIds.value)
  return allQuestions.value
    .filter(q => map.has(q.id))
    .reduce((sum, q) => sum + q.score, 0)
})

const submitQuickGenerate = async () => {
  if (!quickForm.value.title) {
    ElMessage.warning('请输入试卷标题')
    return
  }
  if (selectedQuestionIds.value.length === 0) {
    ElMessage.warning('请至少勾选一道题目')
    return
  }

  generating.value = true
  try {
    const res = await paperApi.generateFromBank({
      title: quickForm.value.title,
      description: quickForm.value.description,
      category: quickForm.value.category,
      suggest_duration: quickForm.value.suggest_duration,
      pass_score: quickForm.value.pass_score,
      question_ids: selectedQuestionIds.value
    })
    ElMessage.success('试卷生成成功！')
    quickGenVisible.value = false
    fetchPapers()
    router.push(`/admin/papers/editor/${res.id}`)
  } catch (e) {
    //
  } finally {
    generating.value = false
  }
}

const getTypeName = (type) => {
  const map = {
    single_choice: '单选',
    multi_choice: '多选',
    true_false: '判断',
    fill_blank: '填空',
    essay: '问答'
  }
  return map[type] || type
}

onMounted(() => {
  fetchPapers()
})
</script>

<style scoped>
.paper-list-container {
  max-width: 1280px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.paper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.paper-card {
  background: white;
  padding: 22px;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.paper-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.4;
}

.category-tag {
  font-size: 11px;
  background: #f1f5f9;
  color: #64748b;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.paper-desc {
  font-size: 12.5px;
  color: #64748b;
  margin: 8px 0 16px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.paper-metrics {
  background: #f8fafc;
  border-radius: 10px;
  padding: 12px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 18px;
}
.metric {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.metric .label {
  color: #64748b;
}

.paper-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
