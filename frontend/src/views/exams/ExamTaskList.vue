<template>
  <AppPage class="exam-task-page">
    <AppPageHeader
      eyebrow="考务管理"
      title="考试发布"
      description="配置试卷、开放时间、授权范围与考试规则"
    />
    <AppPanel title="考务排期列表" :description="`共 ${filteredTaskList.length} 项考试任务`" flush>
      <AppToolbar>
        <div class="toolbar-filters">
          <!-- 授权范围筛选 -->
          <a-select
            v-model="filterScope"
            placeholder="全部授权范围"
            allow-clear
            class="scope-select"
          >
            <a-option label="全员公开" value="ALL" />
            <a-option label="指定部门" value="DEPT" />
            <a-option label="指定人员" value="USER" />
          </a-select>

          <!-- 搜索框 -->
          <a-input
            v-model="searchKeyword"
            placeholder="搜索考试名称或绑定试卷"
            allow-clear
            class="search-input"
          >
            <template #prefix><icon-search /></template>
          </a-input>

        </div>
        <template #actions>
          <div class="action-btn-group">
            <a-button @click="fetchTasks">
              <template #icon><icon-refresh /></template>刷新
            </a-button>
            <a-button type="primary" class="new-btn" @click="openCreateDialog">
              <template #icon><icon-plus /></template>发布新考试
            </a-button>
          </div>
        </template>
      </AppToolbar>

      <!-- 考务数据表格 -->
      <div class="table-wrapper">
        <a-table
          :columns="taskColumns"
          :data="filteredTaskList"
          :loading="loading"
          :pagination="false"
          row-key="id"
          class="custom-data-table"
        >
          <template #task="{ record }">
              <div class="task-title-text">{{ record.title }}</div>
              <div class="task-desc-text">{{ record.description || '无补充说明' }}</div>
          </template>
          <template #paper="{ record }">
              <span class="paper-title-text">{{ record.paper_title }}</span>
              <span class="paper-score-text">满分: {{ record.total_score }} 分</span>
          </template>

          <!-- 授权参考范围 -->
          <template #scope="{ record }">
              <div v-if="record.scope_type === 'ALL'">
                <span class="type-pill pill-all">全员公开</span>
              </div>
              <div v-else-if="record.scope_type === 'DEPT'">
                <a-tooltip
                  :content="record.target_dept_names?.join('、') || '已指定部门'"
                  position="top"
                >
                  <span class="type-pill pill-dept cursor-pointer">
                    指定部门 ({{ record.target_dept_ids?.length || 0 }}个)
                  </span>
                </a-tooltip>
              </div>
              <div v-else-if="record.scope_type === 'USER'">
                <a-tooltip
                  :content="record.target_user_names?.join('、') || '已指定人员'"
                  position="top"
                >
                  <span class="type-pill pill-user cursor-pointer">
                    指定人员 ({{ record.target_user_ids?.length || 0 }}人)
                  </span>
                </a-tooltip>
              </div>
          </template>

          <!-- 开放起止时间段 -->
          <template #time="{ record }">
              <div class="time-scope-display">
                <template v-if="record.start_time || record.end_time">
                  <div>起：{{ formatDate(record.start_time) }}</div>
                  <div :class="isExpired(record.end_time) ? 'text-rose-500 font-medium' : ''">
                    止：{{ formatDate(record.end_time) }}
                    <span v-if="isExpired(record.end_time)" class="ml-1 text-rose-500">(已截止)</span>
                  </div>
                </template>
                <span v-else class="text-emerald-600 font-medium">永久开放有效</span>
              </div>
          </template>

          <!-- 考试规则 -->
          <template #rules="{ record }">
              <div class="rule-box">
                <span>限时: <strong>{{ record.duration_minutes }}</strong> 分钟 | 及格: <strong>{{ record.pass_score }}</strong>分</span>
                <span>重考: <strong>{{ record.max_retries }}</strong> 次 | 详情: <strong :class="record.show_result_immediately ? 'text-emerald-600' : 'text-slate-400'">{{ record.show_result_immediately ? '开放' : '保密' }}</strong></span>
              </div>
          </template>

          <!-- 操作区 -->
          <template #operations="{ record }">
              <div class="table-ops">
                <a-button type="text" status="warning" size="mini" @click="openExtendDialog(record)">
                  延期时间
                </a-button>
                <a-button type="text" size="mini" @click="openAbsenteesDialog(record)">
                  缺考名单
                </a-button>
                <a-button type="text" size="mini" @click="openEditDialog(record)">
                  编辑
                </a-button>
                <a-button type="text" status="danger" size="mini" @click="handleDelete(record.id)">
                  删除
                </a-button>
              </div>
          </template>
        </a-table>
      </div>

      <!-- 底部统计 -->
      <template #footer>
        <span class="footer-total">共 {{ filteredTaskList.length }} 项考务发布记录</span>
      </template>
    </AppPanel>

    <!-- 发布/编辑考试弹窗 -->
    <a-modal
      v-model:visible="dialogVisible"
      :title="isEdit ? '编辑考务任务' : '发布新考务任务'"
      width="640px"
      unmount-on-close
    >
      <a-form :model="form" :label-col-props="{ span: 5 }" :wrapper-col-props="{ span: 19 }" class="pr-4">
        <a-form-item label="选择绑定试卷" required>
          <a-select v-model="form.paper_id" placeholder="请选择已设计的试卷" class="w-full" @change="onPaperSelect">
            <a-option
              v-for="p in papers"
              :key="p.id"
              :label="`${p.title} (总分: ${p.total_score}分)`"
              :value="p.id"
            />
          </a-select>
        </a-form-item>

        <a-form-item label="考试任务名称" required>
          <a-input v-model="form.title" placeholder="例如：2026年企业安全与合规知识通识考试" />
        </a-form-item>

        <a-form-item label="考务说明">
          <a-textarea v-model="form.description" :rows="2" placeholder="填写给考生的注意事项及考核要求..." />
        </a-form-item>

        <!-- 考试有效起止时间段配置 -->
        <div class="time-scope-box p-3.5 bg-blue-50/40 rounded-lg border border-blue-100 mb-4">
          <a-form-item label="开放时间设置" required class="!mb-2">
            <a-radio-group v-model="timeMode">
              <a-radio value="forever">永久有效（随时可考）</a-radio>
              <a-radio value="range">指定开放起止时间段</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="起止有效时间" v-if="timeMode === 'range'" class="!mb-0">
            <a-range-picker
              v-model="dateRange"
              show-time
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DDTHH:mm:ss"
              class="w-full"
            />
            <div class="text-xs text-slate-400 mt-1">考生仅可在该时间窗口内进入考场作答；到期未作答将判定为缺考。</div>
          </a-form-item>
        </div>

        <!-- 参考人员授权范围 (全部平铺展示，不折叠) -->
        <div class="auth-scope-box p-3.5 bg-slate-50 rounded-lg border border-slate-200 mb-4">
          <a-form-item label="参考授权范围" required class="!mb-2">
            <a-radio-group v-model="form.scope_type">
              <a-radio value="ALL">全员公开 (全公司均可参考)</a-radio>
              <a-radio value="DEPT">指定部门</a-radio>
              <a-radio value="USER">指定人员</a-radio>
            </a-radio-group>
          </a-form-item>

          <!-- 按部门指定（所有已选部门全部平铺展示，不折叠） -->
          <a-form-item label="选择授权部门" v-if="form.scope_type === 'DEPT'" class="!mb-0">
            <a-tree-select
              v-model="form.target_dept_ids"
              :data="deptTreeData"
              :field-names="{ key: 'id', title: 'name', children: 'children' }"
              multiple
              tree-checkable
              tree-checked-strategy="all"
              :max-tag-count="3"
              placeholder="请勾选允许参考的目标部门"
              class="w-full"
            />
            <div class="text-xs text-slate-400 mt-1">勾选父部门会自动包含并勾选全部下级部门；保存时仅记录最上层授权范围。</div>
          </a-form-item>

          <!-- 按人员指定（所有已选人员全部平铺展示，不折叠） -->
          <a-form-item label="选择指定人员" v-if="form.scope_type === 'USER'" class="!mb-0">
            <a-select
              v-model="form.target_user_ids"
              multiple
              allow-search
              placeholder="可按姓名或工号搜索并勾选人员"
              class="w-full"
            >
              <a-option
                v-for="u in allUsers"
                :key="u.id"
                :label="`${u.full_name} (${u.email || u.username})`"
                :value="u.id"
              />
            </a-select>
          </a-form-item>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <a-form-item label="答题限时" required>
            <a-input-number v-model="form.duration_minutes" :min="5" :max="300" /> <span class="ml-2 text-sm text-slate-500">分钟</span>
          </a-form-item>

          <a-form-item label="及格分数线" required>
            <a-input-number v-model="form.pass_score" :min="1" :max="1000" /> <span class="ml-2 text-sm text-slate-500">分</span>
          </a-form-item>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <a-form-item label="允许重考次数">
            <a-input-number v-model="form.max_retries" :min="1" :max="10" /> <span class="ml-2 text-sm text-slate-500">次</span>
          </a-form-item>

          <a-form-item label="选项随机乱序">
            <a-switch v-model="form.shuffle_options" checked-text="开启" unchecked-text="关闭" />
          </a-form-item>
        </div>

        <!-- 防作弊与切屏限制设置 -->
        <div class="p-3.5 bg-slate-50 rounded-lg border border-slate-200 mb-4">
          <a-form-item label="防切屏作弊设置" class="!mb-2">
            <a-radio-group v-model="screenSwitchMode">
              <a-radio value="unlimited">不限制切屏 (适合日常自测/培训)</a-radio>
              <a-radio value="limited">限制切屏次数 (正规考试防作弊)</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="最大允许切屏" v-if="screenSwitchMode === 'limited'" class="!mb-0">
            <a-input-number v-model="form.max_screen_switch" :min="1" :max="20" /> <span class="ml-2 text-sm text-slate-500">次 (超限后系统将自动强制收卷)</span>
          </a-form-item>
        </div>

        <!-- 考卷详情与解析查看权限设置 -->
        <div class="p-3.5 bg-blue-50/30 rounded-lg border border-blue-100 mb-4">
          <a-form-item label="考后详情权限" class="!mb-0">
            <a-radio-group v-model="form.show_result_immediately">
              <a-radio :value="true">
                <span class="font-medium text-slate-700">允许查看 (公开模式)</span>
                <span class="text-xs text-slate-400 ml-1">—— 考生交卷后可查看做错的题目及答案解析</span>
              </a-radio>
              <a-radio :value="false">
                <span class="font-medium text-slate-700">禁止查看 (保密模式)</span>
                <span class="text-xs text-slate-400 ml-1">—— 仅展示最终得分，不公开考卷明细与答案</span>
              </a-radio>
            </a-radio-group>
          </a-form-item>
        </div>
      </a-form>

      <template #footer>
        <a-button @click="dialogVisible = false">取消</a-button>
        <a-button type="primary" :loading="saving" @click="submitSave">
          {{ isEdit ? '保存修改' : '确认发布' }}
        </a-button>
      </template>
    </a-modal>

    <!-- 延期考试时间弹窗 -->
    <a-modal v-model:visible="extendVisible" title="考务时间延期 / 补考设置" width="480px">
      <div class="py-2">
        <p class="text-sm text-slate-700 mb-3">
          正在为【<strong>{{ currentExamTask?.title }}</strong>】延长作答截止时间。
        </p>

        <div class="mb-4">
          <div class="text-xs text-slate-500 mb-1">快捷延长周期：</div>
          <div class="flex gap-2">
            <a-button size="small" @click="quickExtendHours(24)">延长 1 天 (24小时)</a-button>
            <a-button size="small" @click="quickExtendHours(72)">延长 3 天</a-button>
            <a-button size="small" @click="quickExtendHours(168)">延长 7 天 (1周)</a-button>
          </div>
        </div>

        <a-form :label-col-props="{ span: 5 }" :wrapper-col-props="{ span: 19 }">
          <a-form-item label="新截止时间" required>
            <a-date-picker
              v-model="newEndTime"
              show-time
              placeholder="选择新的截止时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DDTHH:mm:ss"
              class="w-full"
            />
          </a-form-item>
        </a-form>
      </div>

      <template #footer>
        <a-button @click="extendVisible = false">取消</a-button>
        <a-button type="primary" :loading="extending" @click="submitExtend">确认延期</a-button>
      </template>
    </a-modal>

    <!-- 缺考与应考名单统计弹窗 -->
    <a-modal v-model:visible="absenteesVisible" title="考务应考与缺考名单统计" width="840px">
      <a-spin :loading="absenteesLoading" class="absentee-spin">
      <div class="py-1">
        <div class="grid grid-cols-3 gap-3 mb-4 text-center">
          <div class="p-3 bg-slate-50 rounded-lg">
            <div class="text-xs text-slate-400">应考总人数</div>
            <div class="text-lg font-bold text-slate-800 mt-0.5">{{ absenteeData.total_eligible }} 人</div>
          </div>
          <div class="p-3 bg-emerald-50 rounded-lg">
            <div class="text-xs text-emerald-600">已参加人数</div>
            <div class="text-lg font-bold text-emerald-600 mt-0.5">{{ absenteeData.total_attended }} 人</div>
          </div>
          <div class="p-3 bg-rose-50 rounded-lg">
            <div class="text-xs text-rose-600">缺考/未作答人数</div>
            <div class="text-lg font-bold text-rose-600 mt-0.5">{{ absenteeData.total_absent }} 人</div>
          </div>
        </div>

        <a-tabs v-model:active-key="activeTab">
          <a-tab-pane :title="`缺考人员名单 (${absenteeData.total_absent})`" key="absent">
            <div v-if="absenteeData.absentees?.length === 0" class="text-center py-8 text-slate-400 text-sm">
              全员均已参加考试，无缺考人员！
            </div>
            <a-table v-else :columns="absenteeColumns" :data="absenteeData.absentees" :pagination="false" :scroll="{ y: 300 }" row-key="id" stripe size="small">
              <template #status><a-tag color="red" size="small">缺考</a-tag></template>
            </a-table>
          </a-tab-pane>

          <a-tab-pane :title="`已参加名单 (${absenteeData.total_attended})`" key="attended">
            <a-table :columns="attendeeColumns" :data="absenteeData.attendees" :pagination="false" :scroll="{ y: 300 }" row-key="id" stripe size="small">
              <template #status><a-tag color="green" size="small">已交卷</a-tag></template>
            </a-table>
          </a-tab-pane>
        </a-tabs>
      </div>
      </a-spin>

      <template #footer>
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400">如需让缺考学员继续作答，可点击「延期时间」为本场考试延长截止时间。</span>
          <a-button @click="absenteesVisible = false">关闭</a-button>
        </div>
      </template>
    </a-modal>
  </AppPage>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { examApi, paperApi, userApi } from '@/api'
import { Message, Modal } from '@arco-design/web-vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'
import AppPanel from '@/components/ui/AppPanel.vue'
import AppToolbar from '@/components/ui/AppToolbar.vue'

const loading = ref(false)
const saving = ref(false)
const taskList = ref([])
const papers = ref([])
const departments = ref([])
const allUsers = ref([])

// 顶部过滤搜索
const filterScope = ref('')
const searchKeyword = ref('')
const taskColumns = [
  { title: 'ID', dataIndex: 'id', width: 70, align: 'center' },
  { title: '考试任务名称', minWidth: 220, slotName: 'task' },
  { title: '绑定试卷', minWidth: 180, slotName: 'paper' },
  { title: '参考授权范围', width: 160, align: 'center', slotName: 'scope' },
  { title: '开放考试时间段', minWidth: 210, slotName: 'time' },
  { title: '考试规则', width: 170, slotName: 'rules' },
  { title: '操作', width: 220, align: 'center', fixed: 'right', slotName: 'operations' },
]
const peopleColumns = [
  { title: '姓名', dataIndex: 'full_name', width: 120 },
  { title: '所属部门', dataIndex: 'department_name', width: 180 },
  { title: '企业邮箱', dataIndex: 'email', minWidth: 200 },
  { title: '状态', width: 90, align: 'center', slotName: 'status' },
]
const absenteeColumns = peopleColumns
const attendeeColumns = peopleColumns

// 发布/编辑
const dialogVisible = ref(false)
const isEdit = ref(false)
const editTaskId = ref(null)
const timeMode = ref('forever') // forever, range
const dateRange = ref([])
const screenSwitchMode = ref('limited') // unlimited, limited

const form = ref({
  title: '',
  paper_id: null,
  description: '',
  start_time: null,
  end_time: null,
  duration_minutes: 60,
  pass_score: 60,
  max_retries: 1,
  max_screen_switch: 3,
  shuffle_options: false,
  show_result_immediately: true,
  scope_type: 'ALL',
  target_dept_ids: [],
  target_user_ids: []
})

// 延期
const extendVisible = ref(false)
const extending = ref(false)
const currentExamTask = ref(null)
const newEndTime = ref('')

// 缺考名单
const absenteesVisible = ref(false)
const absenteesLoading = ref(false)
const activeTab = ref('absent')
const absenteeData = ref({
  total_eligible: 0,
  total_attended: 0,
  total_absent: 0,
  absentees: [],
  attendees: []
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await examApi.getTasks()
    taskList.value = res
  } finally {
    loading.value = false
  }
}

const fetchMetadata = async () => {
  const [paperRes, deptRes, userRes] = await Promise.all([
    paperApi.getPapers(),
    userApi.getDepartments(),
    userApi.getUsers()
  ])
  papers.value = paperRes
  departments.value = deptRes
  allUsers.value = userRes
}

// 客户端多维过滤
const filteredTaskList = computed(() => {
  let list = taskList.value
  if (filterScope.value) {
    list = list.filter(t => t.scope_type === filterScope.value)
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(t =>
      t.title?.toLowerCase().includes(kw) ||
      t.paper_title?.toLowerCase().includes(kw)
    )
  }
  return list
})

// 部门树形
const deptTreeData = computed(() => {
  const map = {}
  const roots = []
  departments.value.forEach(d => {
    map[d.id] = { ...d, children: [] }
  })
  departments.value.forEach(d => {
    if (d.parent_id && map[d.parent_id]) {
      map[d.parent_id].children.push(map[d.id])
    } else {
      roots.push(map[d.id])
    }
  })
  return roots
})

const collectDeptSubtreeIds = (deptId) => {
  const ids = []
  const seen = new Set()
  const stack = [deptId]
  while (stack.length) {
    const currentId = stack.pop()
    if (seen.has(currentId)) continue
    seen.add(currentId)
    ids.push(currentId)
    departments.value.forEach(dept => {
      if (dept.parent_id === currentId) stack.push(dept.id)
    })
  }
  return ids
}

const expandDeptSelections = (selectedIds) => {
  const expanded = new Set()
  ;(selectedIds || []).forEach(id => collectDeptSubtreeIds(id).forEach(childId => expanded.add(childId)))
  return [...expanded]
}

const compressDeptSelections = (selectedIds) => {
  const selected = new Set(selectedIds || [])
  const deptMap = new Map(departments.value.map(dept => [dept.id, dept]))
  return [...selected].filter(id => {
    let parentId = deptMap.get(id)?.parent_id
    const visited = new Set()
    while (parentId && !visited.has(parentId)) {
      if (selected.has(parentId)) return false
      visited.add(parentId)
      parentId = deptMap.get(parentId)?.parent_id
    }
    return true
  })
}

const handleDeptCheck = (node, state) => {
  const selected = new Set(state.checkedKeys || [])
  const subtreeIds = collectDeptSubtreeIds(node.id)
  if (selected.has(node.id)) {
    subtreeIds.forEach(id => selected.add(id))
  } else {
    subtreeIds.forEach(id => selected.delete(id))
  }
  // 已选父部门不能单独排除某个子部门，确保界面与实际授权口径一致。
  ;[...selected].forEach(id => collectDeptSubtreeIds(id).forEach(childId => selected.add(childId)))
  form.value.target_dept_ids = [...selected]
}

const openCreateDialog = () => {
  isEdit.value = false
  editTaskId.value = null
  timeMode.value = 'forever'
  dateRange.value = []
  screenSwitchMode.value = 'unlimited'
  form.value = {
    title: '',
    paper_id: papers.value.length ? papers.value[0].id : null,
    description: '',
    start_time: null,
    end_time: null,
    duration_minutes: 60,
    pass_score: 60,
    max_retries: 1,
    max_screen_switch: 0,
    shuffle_options: false,
    show_result_immediately: true,
    scope_type: 'ALL',
    target_dept_ids: [],
    target_user_ids: []
  }
  if (papers.value.length) {
    onPaperSelect(papers.value[0].id)
  }
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEdit.value = true
  editTaskId.value = row.id
  screenSwitchMode.value = (row.max_screen_switch && row.max_screen_switch > 0) ? 'limited' : 'unlimited'
  if (row.start_time && row.end_time) {
    timeMode.value = 'range'
    dateRange.value = [row.start_time, row.end_time]
  } else {
    timeMode.value = 'forever'
    dateRange.value = []
  }
  form.value = {
    title: row.title,
    paper_id: row.paper_id,
    description: row.description || '',
    start_time: row.start_time,
    end_time: row.end_time,
    duration_minutes: row.duration_minutes,
    pass_score: row.pass_score,
    max_retries: row.max_retries,
    max_screen_switch: row.max_screen_switch || 0,
    shuffle_options: row.shuffle_options,
    show_result_immediately: row.show_result_immediately,
    scope_type: row.scope_type || 'ALL',
    target_dept_ids: expandDeptSelections(row.target_dept_ids || []),
    target_user_ids: row.target_user_ids || []
  }
  dialogVisible.value = true
}

const onPaperSelect = (paperId) => {
  const p = papers.value.find(item => item.id === paperId)
  if (p) {
    if (!form.value.title || form.value.title.endsWith(' - 考核任务')) {
      form.value.title = p.title + ' - 考核任务'
    }
    form.value.pass_score = p.pass_score || 60
    form.value.duration_minutes = p.suggest_duration || 60
  }
}

const submitSave = async () => {
  if (!form.value.title || !form.value.paper_id) {
    Message.warning('请填写考试标题并选择试卷')
    return
  }

  if (timeMode.value === 'range') {
    if (!dateRange.value || dateRange.value.length < 2) {
      Message.warning('请选择考试开放起止时间范围')
      return
    }
    form.value.start_time = dateRange.value[0]
    form.value.end_time = dateRange.value[1]
  } else {
    form.value.start_time = null
    form.value.end_time = null
  }

  // 若选择不限制切屏，则将最大切屏次数置为 0
  if (screenSwitchMode.value === 'unlimited') {
    form.value.max_screen_switch = 0
  } else if (!form.value.max_screen_switch || form.value.max_screen_switch <= 0) {
    form.value.max_screen_switch = 3
  }

  if (form.value.scope_type === 'DEPT' && (!form.value.target_dept_ids || !form.value.target_dept_ids.length)) {
    Message.warning('请至少勾选一个授权参考的目标部门')
    return
  }
  if (form.value.scope_type === 'USER' && (!form.value.target_user_ids || !form.value.target_user_ids.length)) {
    Message.warning('请至少指定一名允许参考的目标员工')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...form.value,
      target_dept_ids: form.value.scope_type === 'DEPT'
        ? compressDeptSelections(form.value.target_dept_ids)
        : []
    }
    if (isEdit.value) {
      await examApi.updateTask(editTaskId.value, payload)
      Message.success('考务任务更新成功！')
    } else {
      await examApi.createTask(payload)
      Message.success('考试任务发布成功！')
    }
    dialogVisible.value = false
    fetchTasks()
  } finally {
    saving.value = false
  }
}

// 延期
const openExtendDialog = (row) => {
  currentExamTask.value = row
  const base = row.end_time ? new Date(row.end_time) : new Date()
  const next24h = new Date(base.getTime() + 24 * 3600 * 1000)
  newEndTime.value = next24h.toISOString().slice(0, 19)
  extendVisible.value = true
}

const quickExtendHours = (hours) => {
  const base = currentExamTask.value?.end_time ? new Date(currentExamTask.value.end_time) : new Date()
  const target = new Date(Math.max(Date.now(), base.getTime()) + hours * 3600 * 1000)
  newEndTime.value = target.toISOString().slice(0, 19)
}

const submitExtend = async () => {
  if (!newEndTime.value) {
    Message.warning('请选择新的截止时间')
    return
  }
  extending.value = true
  try {
    await examApi.extendTaskTime(currentExamTask.value.id, { end_time: newEndTime.value })
    Message.success('考务时间已成功延长！')
    extendVisible.value = false
    fetchTasks()
  } finally {
    extending.value = false
  }
}

// 缺考名单查看
const openAbsenteesDialog = async (row) => {
  currentExamTask.value = row
  absenteesVisible.value = true
  absenteesLoading.value = true
  activeTab.value = 'absent'
  try {
    const res = await examApi.getAbsentees(row.id)
    absenteeData.value = res
  } finally {
    absenteesLoading.value = false
  }
}

const handleDelete = (id) => {
  Modal.warning({
    title: '删除确认',
    content: '确定要删除该考务任务吗？已答卷考生的历史成绩记录也将一并清除。',
    hideCancel: false,
    okText: '删除任务',
    onOk: async () => {
      await examApi.deleteTask(id)
      Message.success('考务任务已删除')
      fetchTasks()
    },
  })
}

const formatDate = (isoStr) => {
  if (!isoStr) return '永久有效'
  const d = new Date(isoStr)
  return d.toLocaleString()
}

const isExpired = (isoStr) => {
  if (!isoStr) return false
  return new Date(isoStr).getTime() < Date.now()
}

onMounted(() => {
  fetchTasks()
  fetchMetadata()
})
</script>

<style scoped>
.exam-task-page {
  --app-page-gap: var(--app-space-4);
}

.toolbar-filters {
  display: flex;
  align-items: center;
  gap: var(--app-space-2);
  flex-wrap: wrap;
}

.scope-select {
  width: 140px;
}
.search-input {
  width: 220px;
}

.action-btn-group {
  display: flex;
  gap: 8px;
  align-items: center;
}
.new-btn {
  font-weight: 600;
}

/* 表格字段样式 */
.task-title-text {
  font-weight: 600;
  color: #1e293b;
  font-size: 13.5px;
}
.task-desc-text {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
}

.paper-title-text {
  font-weight: 600;
  color: #334155;
  font-size: 13px;
  display: block;
}
.paper-score-text {
  font-size: 12px;
  color: #2563eb;
  margin-top: 2px;
  display: block;
}

/* 授权范围胶囊 */
.type-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 10px;
  border-radius: var(--app-radius-control);
  font-size: 12px;
  font-weight: 500;
}
.pill-all  { background: #eff6ff; color: #2563eb; }
.pill-dept { background: #ecfdf5; color: #059669; }
.pill-user { background: #fffbeb; color: #d97706; }

.time-scope-display {
  font-size: 12px;
  color: #475569;
  line-height: 1.5;
}

.rule-box {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #475569;
}

.table-ops {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
}

.footer-total {
  font-size: 12px;
  color: #64748b;
}
.absentee-spin { width: 100%; }
</style>
