<template>
  <AppPage class="paper-list-container">
    <AppPageHeader
      eyebrow="内容资产"
      title="试卷管理与组卷中心"
      description="支持可视化设计与题库快速组卷，统一配置题型和分值规则"
    >
      <template #icon>
          <FileText :size="20" class="text-blue-600" />
      </template>
      <template #actions>
        <a-button type="outline" status="success" @click="openQuickGenerateDialog">
          <Sparkles :size="14" class="mr-1" /> 从题库快速选题组卷
        </a-button>
        <a-button type="primary" @click="createEmptyPaper">
          <template #icon><icon-plus /></template>可视化创建试卷
        </a-button>
      </template>
    </AppPageHeader>

    <!-- 试卷卡片列表 -->
    <AppState v-if="loading" loading loading-text="正在加载试卷库..." />

    <AppState
      v-else-if="paperList.length === 0"
      title="暂无试卷"
      description="创建第一份考核试卷后，可在此统一管理和发布"
    />

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
          <a-button type="outline" class="flex-1" @click="editPaper(paper.id)">
            <template #icon><icon-edit /></template>编辑设计试卷
          </a-button>
          <a-button type="text" status="danger" @click="deletePaper(paper.id)">
            删除
          </a-button>
        </div>
      </div>
    </div>

    <!-- 从题库选题一键组卷弹窗 -->
    <a-modal v-model:visible="quickGenVisible" title="从题库快速选题组卷" width="840px">
      <div class="p-2">
        <a-form :model="quickForm" :label-col-props="{ span: 4 }" :wrapper-col-props="{ span: 20 }">
          <a-form-item label="试卷标题" required>
            <a-input v-model="quickForm.title" placeholder="例如：2026年企业新员工入职考试试卷" />
          </a-form-item>
          <div class="grid grid-cols-2 gap-4">
            <a-form-item label="建议用时">
              <a-input-number v-model="quickForm.suggest_duration" :min="5" :max="180" /> 分钟
            </a-form-item>
            <a-form-item label="及格分数线">
              <a-input-number v-model="quickForm.pass_score" :min="1" :max="1000" /> 分
            </a-form-item>
          </div>
        </a-form>

        <div class="text-xs text-slate-500 font-semibold mb-2 mt-4">勾选要加入试卷的题目：</div>
        <a-table
          v-model:selected-keys="selectedQuestionIds"
          :columns="questionColumns"
          :data="allQuestions"
          :loading="questionsLoading"
          :pagination="false"
          :row-selection="{ type: 'checkbox', showCheckedAll: true }"
          :scroll="{ y: 300 }"
          row-key="id"
          stripe
        >
          <template #type="{ record }">{{ getTypeName(record.type) }}</template>
          <template #score="{ record }">{{ record.score }}分</template>
        </a-table>
        <div class="text-right text-xs text-slate-500 mt-2">
          已勾选 <strong>{{ selectedQuestionIds.length }}</strong> 道题目，预估总分：<strong>{{ selectedTotalScore }}</strong> 分
        </div>
      </div>

      <template #footer>
        <a-button @click="quickGenVisible = false">取消</a-button>
        <a-button type="primary" :loading="generating" @click="submitQuickGenerate">一键生成试卷</a-button>
      </template>
    </a-modal>
  </AppPage>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { paperApi, questionApi } from '@/api'
import { Message, Modal } from '@arco-design/web-vue'
import { FileText, Sparkles } from 'lucide-vue-next'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppState from '@/components/ui/AppState.vue'

const router = useRouter()
const loading = ref(false)
const paperList = ref([])

// 快速组卷
const quickGenVisible = ref(false)
const questionsLoading = ref(false)
const generating = ref(false)
const allQuestions = ref([])
const selectedQuestionIds = ref([])
const questionColumns = [
  { title: 'ID', dataIndex: 'id', width: 60, align: 'center' },
  { title: '题型', dataIndex: 'type', width: 90, slotName: 'type' },
  { title: '题干', dataIndex: 'title', ellipsis: true, tooltip: true },
  { title: '分值', dataIndex: 'score', width: 70, align: 'center', slotName: 'score' },
]

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
  Modal.warning({
    title: '删除确认',
    content: '确定要删除该试卷吗？若已有发布的考务关联将受影响。',
    hideCancel: false,
    okText: '删除试卷',
    cancelText: '取消',
    onOk: async () => {
      await paperApi.deletePaper(id)
      Message.success('试卷已删除')
      fetchPapers()
    },
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

const selectedTotalScore = computed(() => {
  const map = new Set(selectedQuestionIds.value)
  return allQuestions.value
    .filter(q => map.has(q.id))
    .reduce((sum, q) => sum + q.score, 0)
})

const submitQuickGenerate = async () => {
  if (!quickForm.value.title) {
    Message.warning('请输入试卷标题')
    return
  }
  if (selectedQuestionIds.value.length === 0) {
    Message.warning('请至少勾选一道题目')
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
    Message.success('试卷生成成功！')
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
  --app-page-gap: var(--app-space-4);
}

.paper-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--app-space-4);
}

.paper-card {
  background: white;
  padding: var(--app-space-5);
  border-radius: var(--app-radius-panel);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.paper-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-1);
  line-height: 1.4;
}

.category-tag {
  font-size: 11px;
  background: #f1f5f9;
  color: var(--color-text-3);
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
  background: var(--color-fill-1);
  border-radius: var(--app-radius-control);
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
  color: var(--color-text-3);
}

.paper-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
