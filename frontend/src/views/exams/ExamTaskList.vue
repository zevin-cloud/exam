<template>
  <div class="exam-task-page">
    <!-- 一体化专业卡片 (参照题库与试题管理设计) -->
    <div class="exam-card app-card">
      <!-- 顶部工具栏 -->
      <div class="card-toolbar">
        <div class="toolbar-left">
          <h3 class="card-title">考务排期列表</h3>
          <span class="count-badge">共 {{ filteredTaskList.length }} 项考试任务</span>
        </div>

        <div class="toolbar-right">
          <!-- 授权范围筛选 -->
          <el-select 
            v-model="filterScope" 
            placeholder="全部授权范围" 
            clearable 
            class="scope-select"
          >
            <el-option label="全员公开" value="ALL" />
            <el-option label="指定部门" value="DEPT" />
            <el-option label="指定人员" value="USER" />
          </el-select>

          <!-- 搜索框 -->
          <el-input 
            v-model="searchKeyword" 
            placeholder="搜索考试名称或绑定试卷" 
            clearable 
            class="search-input"
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
            <el-button @click="fetchTasks">
              刷新
            </el-button>
            <el-button type="primary" class="new-btn" @click="openCreateDialog">
              + 发布新考试
            </el-button>
          </div>
        </div>
      </div>

      <!-- 考务数据表格 -->
      <div class="table-wrapper">
        <el-table 
          :data="filteredTaskList" 
          v-loading="loading" 
          style="width: 100%" 
          class="custom-data-table"
        >
          <el-table-column prop="id" label="ID" width="70" align="center" />
          
          <el-table-column label="考试任务名称" min-width="220">
            <template #default="{ row }">
              <div class="task-title-text">{{ row.title }}</div>
              <div class="task-desc-text">{{ row.description || '无补充说明' }}</div>
            </template>
          </el-table-column>

          <el-table-column label="绑定试卷" min-width="180">
            <template #default="{ row }">
              <span class="paper-title-text">{{ row.paper_title }}</span>
              <span class="paper-score-text">满分: {{ row.total_score }} 分</span>
            </template>
          </el-table-column>

          <!-- 授权参考范围 -->
          <el-table-column label="参考授权范围" width="160" align="center">
            <template #default="{ row }">
              <div v-if="row.scope_type === 'ALL'">
                <span class="type-pill pill-all">全员公开</span>
              </div>
              <div v-else-if="row.scope_type === 'DEPT'">
                <el-tooltip 
                  :content="row.target_dept_names?.join('、') || '已指定部门'" 
                  placement="top"
                >
                  <span class="type-pill pill-dept cursor-pointer">
                    指定部门 ({{ row.target_dept_ids?.length || 0 }}个)
                  </span>
                </el-tooltip>
              </div>
              <div v-else-if="row.scope_type === 'USER'">
                <el-tooltip 
                  :content="row.target_user_names?.join('、') || '已指定人员'" 
                  placement="top"
                >
                  <span class="type-pill pill-user cursor-pointer">
                    指定人员 ({{ row.target_user_ids?.length || 0 }}人)
                  </span>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>

          <!-- 开放起止时间段 -->
          <el-table-column label="开放考试时间段" min-width="210">
            <template #default="{ row }">
              <div class="time-scope-display">
                <template v-if="row.start_time || row.end_time">
                  <div>起：{{ formatDate(row.start_time) }}</div>
                  <div :class="isExpired(row.end_time) ? 'text-rose-500 font-medium' : ''">
                    止：{{ formatDate(row.end_time) }}
                    <span v-if="isExpired(row.end_time)" class="ml-1 text-rose-500">(已截止)</span>
                  </div>
                </template>
                <span v-else class="text-emerald-600 font-medium">永久开放有效</span>
              </div>
            </template>
          </el-table-column>

          <!-- 考试规则 -->
          <el-table-column label="考试规则" width="170">
            <template #default="{ row }">
              <div class="rule-box">
                <span>限时: <strong>{{ row.duration_minutes }}</strong> 分钟 | 及格: <strong>{{ row.pass_score }}</strong>分</span>
                <span>重考: <strong>{{ row.max_retries }}</strong> 次 | 详情: <strong :class="row.show_result_immediately ? 'text-emerald-600' : 'text-slate-400'">{{ row.show_result_immediately ? '开放' : '保密' }}</strong></span>
              </div>
            </template>
          </el-table-column>

          <!-- 操作区 -->
          <el-table-column label="操作" width="220" align="center" fixed="right">
            <template #default="{ row }">
              <div class="table-ops">
                <el-button link type="warning" size="small" @click="openExtendDialog(row)">
                  延期时间
                </el-button>
                <el-button link type="primary" size="small" @click="openAbsenteesDialog(row)">
                  缺考名单
                </el-button>
                <el-button link type="primary" size="small" @click="openEditDialog(row)">
                  编辑
                </el-button>
                <el-button link type="danger" size="small" @click="handleDelete(row.id)">
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 底部统计 -->
      <div class="card-footer">
        <span class="footer-total">共 {{ filteredTaskList.length }} 项考务发布记录</span>
      </div>
    </div>

    <!-- 发布/编辑考试弹窗 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="isEdit ? '编辑考务任务' : '发布新考务任务'" 
      width="680px" 
      destroy-on-close
    >
      <el-form :model="form" label-width="120px" class="pr-4">
        <el-form-item label="选择绑定试卷" required>
          <el-select v-model="form.paper_id" placeholder="请选择已设计的试卷" class="w-full" @change="onPaperSelect">
            <el-option 
              v-for="p in papers" 
              :key="p.id" 
              :label="`${p.title} (总分: ${p.total_score}分)`" 
              :value="p.id" 
            />
          </el-select>
        </el-form-item>

        <el-form-item label="考试任务名称" required>
          <el-input v-model="form.title" placeholder="例如：2026年企业安全与合规知识通识考试" />
        </el-form-item>

        <el-form-item label="考务说明">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="填写给考生的注意事项及考核要求..." />
        </el-form-item>

        <!-- 考试有效起止时间段配置 -->
        <div class="time-scope-box p-3.5 bg-blue-50/40 rounded-lg border border-blue-100 mb-4">
          <el-form-item label="开放时间设置" required class="!mb-2">
            <el-radio-group v-model="timeMode">
              <el-radio value="forever">永久有效（随时可考）</el-radio>
              <el-radio value="range">指定开放起止时间段</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="起止有效时间" v-if="timeMode === 'range'" class="!mb-0">
            <el-date-picker
              v-model="dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="截止时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DDTHH:mm:ss"
              class="w-full"
            />
            <div class="text-xs text-slate-400 mt-1">考生仅可在该时间窗口内进入考场作答；到期未作答将判定为缺考。</div>
          </el-form-item>
        </div>

        <!-- 参考人员授权范围 (全部平铺展示，不折叠) -->
        <div class="auth-scope-box p-3.5 bg-slate-50 rounded-lg border border-slate-200 mb-4">
          <el-form-item label="参考授权范围" required class="!mb-2">
            <el-radio-group v-model="form.scope_type">
              <el-radio value="ALL">全员公开 (全公司均可参考)</el-radio>
              <el-radio value="DEPT">指定部门</el-radio>
              <el-radio value="USER">指定人员</el-radio>
            </el-radio-group>
          </el-form-item>

          <!-- 按部门指定（所有已选部门全部平铺展示，不折叠） -->
          <el-form-item label="选择授权部门" v-if="form.scope_type === 'DEPT'" class="!mb-0">
            <el-tree-select
              v-model="form.target_dept_ids"
              :data="deptTreeData"
              :props="{ label: 'name', value: 'id', children: 'children' }"
              node-key="id"
              value-key="id"
              :render-after-expand="false"
              multiple
              show-checkbox
              check-strictly
              placeholder="请勾选允许参考的目标部门"
              class="w-full"
            />
            <div class="text-xs text-slate-400 mt-1">选中的部门及其下级子部门的员工均有权限参与本次考试。</div>
          </el-form-item>

          <!-- 按人员指定（所有已选人员全部平铺展示，不折叠） -->
          <el-form-item label="选择指定人员" v-if="form.scope_type === 'USER'" class="!mb-0">
            <el-select
              v-model="form.target_user_ids"
              multiple
              filterable
              placeholder="可按姓名或工号搜索并勾选人员"
              class="w-full"
            >
              <el-option
                v-for="u in allUsers"
                :key="u.id"
                :label="`${u.full_name} (${u.email || u.username})`"
                :value="u.id"
              />
            </el-select>
          </el-form-item>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="答题限时" required>
            <el-input-number v-model="form.duration_minutes" :min="5" :max="300" /> <span class="ml-2 text-sm text-slate-500">分钟</span>
          </el-form-item>

          <el-form-item label="及格分数线" required>
            <el-input-number v-model="form.pass_score" :min="1" :max="1000" /> <span class="ml-2 text-sm text-slate-500">分</span>
          </el-form-item>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <el-form-item label="允许重考次数">
            <el-input-number v-model="form.max_retries" :min="1" :max="10" /> <span class="ml-2 text-sm text-slate-500">次</span>
          </el-form-item>

          <el-form-item label="选项随机乱序">
            <el-switch v-model="form.shuffle_options" active-text="开启" inactive-text="关闭" />
          </el-form-item>
        </div>

        <!-- 防作弊与切屏限制设置 -->
        <div class="p-3.5 bg-slate-50 rounded-lg border border-slate-200 mb-4">
          <el-form-item label="防切屏作弊设置" class="!mb-2">
            <el-radio-group v-model="screenSwitchMode">
              <el-radio value="unlimited">不限制切屏 (适合日常自测/培训)</el-radio>
              <el-radio value="limited">限制切屏次数 (正规考试防作弊)</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="最大允许切屏" v-if="screenSwitchMode === 'limited'" class="!mb-0">
            <el-input-number v-model="form.max_screen_switch" :min="1" :max="20" /> <span class="ml-2 text-sm text-slate-500">次 (超限后系统将自动强制收卷)</span>
          </el-form-item>
        </div>

        <!-- 考卷详情与解析查看权限设置 -->
        <div class="p-3.5 bg-blue-50/30 rounded-lg border border-blue-100 mb-4">
          <el-form-item label="考后详情权限" class="!mb-0">
            <el-radio-group v-model="form.show_result_immediately">
              <el-radio :value="true">
                <span class="font-medium text-slate-700">允许查看 (公开模式)</span>
                <span class="text-xs text-slate-400 ml-1">—— 考生交卷后可查看做错的题目及答案解析</span>
              </el-radio>
              <el-radio :value="false">
                <span class="font-medium text-slate-700">禁止查看 (保密模式)</span>
                <span class="text-xs text-slate-400 ml-1">—— 仅展示最终得分，不公开考卷明细与答案</span>
              </el-radio>
            </el-radio-group>
          </el-form-item>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitSave">
          {{ isEdit ? '保存修改' : '确认发布' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 延期考试时间弹窗 -->
    <el-dialog v-model="extendVisible" title="考务时间延期 / 补考设置" width="480px">
      <div class="py-2">
        <p class="text-sm text-slate-700 mb-3">
          正在为【<strong>{{ currentExamTask?.title }}</strong>】延长作答截止时间。
        </p>

        <div class="mb-4">
          <div class="text-xs text-slate-500 mb-1">快捷延长周期：</div>
          <div class="flex gap-2">
            <el-button size="small" @click="quickExtendHours(24)">延长 1 天 (24小时)</el-button>
            <el-button size="small" @click="quickExtendHours(72)">延长 3 天</el-button>
            <el-button size="small" @click="quickExtendHours(168)">延长 7 天 (1周)</el-button>
          </div>
        </div>

        <el-form label-width="90px">
          <el-form-item label="新截止时间" required>
            <el-date-picker
              v-model="newEndTime"
              type="datetime"
              placeholder="选择新的截止时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DDTHH:mm:ss"
              class="w-full"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="extendVisible = false">取消</el-button>
        <el-button type="primary" :loading="extending" @click="submitExtend">确认延期</el-button>
      </template>
    </el-dialog>

    <!-- 缺考与应考名单统计弹窗 -->
    <el-dialog v-model="absenteesVisible" title="考务应考与缺考名单统计" width="700px">
      <div v-loading="absenteesLoading" class="py-1">
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

        <el-tabs v-model="activeTab">
          <el-tab-pane :label="`缺考人员名单 (${absenteeData.total_absent})`" name="absent">
            <div v-if="absenteeData.absentees?.length === 0" class="text-center py-8 text-slate-400 text-sm">
              全员均已参加考试，无缺考人员！
            </div>
            <el-table v-else :data="absenteeData.absentees" max-height="300" stripe size="small">
              <el-table-column prop="full_name" label="姓名" width="120" />
              <el-table-column prop="department_name" label="所属部门" width="180" />
              <el-table-column prop="email" label="企业邮箱" min-width="200" />
              <el-table-column label="状态" width="90" align="center">
                <template #default>
                  <el-tag type="danger" size="small">缺考</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane :label="`已参加名单 (${absenteeData.total_attended})`" name="attended">
            <el-table :data="absenteeData.attendees" max-height="300" stripe size="small">
              <el-table-column prop="full_name" label="姓名" width="120" />
              <el-table-column prop="department_name" label="所属部门" width="180" />
              <el-table-column prop="email" label="企业邮箱" min-width="200" />
              <el-table-column label="状态" width="90" align="center">
                <template #default>
                  <el-tag type="success" size="small">已交卷</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>

      <template #footer>
        <div class="flex justify-between items-center">
          <span class="text-xs text-slate-400">如需让缺考学员继续作答，可点击「延期时间」为本场考试延长截止时间。</span>
          <el-button @click="absenteesVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { examApi, paperApi, userApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const taskList = ref([])
const papers = ref([])
const departments = ref([])
const allUsers = ref([])

// 顶部过滤搜索
const filterScope = ref('')
const searchKeyword = ref('')

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
    target_dept_ids: row.target_dept_ids || [],
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
    ElMessage.warning('请填写考试标题并选择试卷')
    return
  }

  if (timeMode.value === 'range') {
    if (!dateRange.value || dateRange.value.length < 2) {
      ElMessage.warning('请选择考试开放起止时间范围')
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
    ElMessage.warning('请至少勾选一个授权参考的目标部门')
    return
  }
  if (form.value.scope_type === 'USER' && (!form.value.target_user_ids || !form.value.target_user_ids.length)) {
    ElMessage.warning('请至少指定一名允许参考的目标员工')
    return
  }

  saving.value = true
  try {
    if (isEdit.value) {
      await examApi.updateTask(editTaskId.value, form.value)
      ElMessage.success('考务任务更新成功！')
    } else {
      await examApi.createTask(form.value)
      ElMessage.success('考试任务发布成功！')
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
    ElMessage.warning('请选择新的截止时间')
    return
  }
  extending.value = true
  try {
    await examApi.extendTaskTime(currentExamTask.value.id, { end_time: newEndTime.value })
    ElMessage.success('考务时间已成功延长！')
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
  ElMessageBox.confirm('确定要删除该考务任务吗？已答卷考生的历史成绩记录也将一并清除。', '删除确认', {
    type: 'warning'
  }).then(async () => {
    await examApi.deleteTask(id)
    ElMessage.success('考务任务已删除')
    fetchTasks()
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
  max-width: 1360px;
  margin: 0 auto;
}

/* 主体卡片 (与题库管理完全一致) */
.exam-card {
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
  border-radius: 6px;
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
  border-radius: 10px;
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
