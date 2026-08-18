<template>
  <div class="org-manage-page">
    <!-- 顶部操作横栏 (去除了 Emoji 图标，改用现代统一矢量图标与干净文字) -->
    <div class="top-action-bar">
      <div class="page-meta">
        <h2 class="page-title">组织架构与成员管理</h2>
        <p class="page-subtitle">统一管理企业部门层级、员工名册与 OneAuth 身份源数据实时对齐</p>
      </div>

      <div class="top-btns flex items-center gap-2.5 flex-wrap">
        <el-button @click="openSSOConfigDialog">
          <Settings :size="14" class="btn-icon" /> 身份源配置
        </el-button>
        <el-button type="info" plain :loading="syncingDept" @click="handleSyncDepartmentsOnly">
          <Building2 :size="14" class="btn-icon" /> 同步部门架构
        </el-button>
        <el-button type="primary" :loading="loadingCandidates" @click="openCandidateUsersDialog">
          <UserPlus :size="14" class="btn-icon" /> 选择同步 OneAuth 成员
        </el-button>
        <el-button type="success" plain :loading="syncingAll" @click="handleSyncAllData">
          <RefreshCw :size="14" class="btn-icon" /> 一键全量同步
        </el-button>
      </div>
    </div>

    <!-- 主体两栏布局：左侧部门树 + 右侧成员列表 -->
    <div class="org-layout-grid mt-4">
      <!-- 左栏：组织架构树卡片 (设置 sticky 保持视口固定不滑移) -->
      <div class="dept-tree-card app-card">
        <div class="dept-card-header">
          <div>
            <h3 class="tree-title">组织架构</h3>
            <p class="tree-subtitle">部门层级与关联</p>
          </div>
          <el-button type="primary" size="small" class="new-dept-btn" @click="openCreateDeptDialog(null)">
            + 新建部门
          </el-button>
        </div>

        <!-- 部门搜索框 -->
        <div class="dept-search-wrap">
          <el-input 
            v-model="deptFilterText" 
            placeholder="搜索部门名称" 
            clearable
            size="default"
          >
            <template #prefix>
              <Search :size="14" class="text-slate-400" />
            </template>
          </el-input>
        </div>

        <!-- 部门树形组件 -->
        <div class="dept-tree-body">
          <div 
            class="all-dept-item" 
            :class="{ 'is-selected': selectedDeptId === null }"
            @click="selectDept(null)"
          >
            <div class="flex items-center gap-2">
              <Folder :size="15" class="text-blue-500" />
              <span class="font-medium text-slate-700">全部部门</span>
            </div>
            <span class="dept-count-badge">{{ users.length }}</span>
          </div>

          <el-tree
            ref="treeRef"
            :data="deptTreeData"
            :props="{ label: 'name', children: 'children' }"
            :filter-node-method="filterNode"
            node-key="id"
            default-expand-all
            highlight-current
            @node-click="handleTreeNodeClick"
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node">
                <div class="node-left">
                  <FolderTree :size="14" class="dept-icon" />
                  <span class="node-label">{{ node.label }}</span>
                </div>

                <div class="node-actions" @click.stop>
                  <el-dropdown trigger="click" @command="(cmd) => handleDeptCommand(cmd, data)">
                    <span class="more-dot">•••</span>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="addChild">+ 添加子部门</el-dropdown-item>
                        <el-dropdown-item command="edit">编辑名称</el-dropdown-item>
                        <el-dropdown-item command="delete" divided class="text-red-500">删除部门...</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- 右栏：全部成员卡片 -->
      <div class="dept-members-card app-card">
        <div class="members-header">
          <div class="header-title-box">
            <h3 class="members-title">{{ selectedDeptName || '全部成员' }}</h3>
            <span class="members-count">共 {{ filteredUsers.length }} 人</span>
          </div>

          <div class="header-action-box">
            <el-input 
              v-model="userSearchKeyword" 
              placeholder="按成员姓名或邮箱搜索" 
              clearable 
              class="user-search-input"
            >
              <template #prefix>
                <Search :size="14" class="text-slate-400" />
              </template>
            </el-input>

            <el-button type="primary" @click="openCreateUserDialog">
              + 添加成员
            </el-button>
          </div>
        </div>

        <!-- 批量操作栏（多选成员时显示） -->
        <transition name="el-fade-in">
          <div v-if="selectedUsers.length > 0" class="batch-bar">
            <div class="batch-left">
              <span class="batch-badge">
                已选中 <strong>{{ selectedUsers.length }}</strong> 位成员
              </span>
            </div>
            <div class="batch-right">
              <el-dropdown trigger="click" @command="handleBatchRoleChange">
                <el-button type="primary" :loading="batchRoleLoading">
                  <ShieldCheck :size="15" class="mr-1.5" />
                  批量设置角色
                  <ChevronDown :size="14" class="ml-1" />
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu class="batch-role-menu">
                    <el-dropdown-item command="student">
                      <div class="batch-role-item">
                        <span class="role-dot student"></span>
                        <div>
                          <div class="role-item-title">考生 / 普通员工</div>
                          <div class="role-item-desc">仅参加考试与查卷 (student)</div>
                        </div>
                      </div>
                    </el-dropdown-item>
                    <el-dropdown-item command="teacher" divided>
                      <div class="batch-role-item">
                        <span class="role-dot teacher"></span>
                        <div>
                          <div class="role-item-title text-amber-600">出题人 / 阅卷老师</div>
                          <div class="role-item-desc">试卷题库与阅卷考务 (teacher)</div>
                        </div>
                      </div>
                    </el-dropdown-item>
                    <el-dropdown-item command="super_admin" divided>
                      <div class="batch-role-item">
                        <span class="role-dot admin"></span>
                        <div>
                          <div class="role-item-title text-rose-600">超级管理员</div>
                          <div class="role-item-desc">全系统配置与管理权限 (super_admin)</div>
                        </div>
                      </div>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>

              <el-button @click="clearUserSelection">
                取消选择
              </el-button>
            </div>
          </div>
        </transition>

        <!-- 成员表格 -->
        <div class="table-container">
          <el-table 
            ref="userTableRef"
            :data="paginatedUsers" 
            style="width: 100%" 
            v-loading="loading"
            row-key="id"
            @selection-change="handleUserSelectionChange"
            class="custom-table"
          >
            <el-table-column type="selection" width="48" align="center" />
            <el-table-column label="成员信息" min-width="220">
              <template #default="{ row }">
                <div class="user-cell">
                  <div class="avatar-cell" :style="{ backgroundColor: getAvatarColor(row.full_name) }">
                    {{ getAvatarText(row.full_name) }}
                  </div>
                  <div class="user-meta-wrap">
                    <div class="user-name-line">
                      <span class="full-name">{{ row.full_name }}</span>
                      <el-tag v-if="row.role === 'super_admin'" type="danger" size="small" effect="plain">超管</el-tag>
                      <el-tag v-else-if="row.role === 'teacher'" type="warning" size="small" effect="plain">出题人</el-tag>
                    </div>
                    <span class="user-email-text">{{ row.email || row.username }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="username" label="工号/用户名" min-width="130" />
            <el-table-column prop="department_name" label="所属部门" min-width="140">
              <template #default="{ row }">
                <span v-if="row.department_name" class="dept-tag-cell">{{ row.department_name }}</span>
                <span v-else class="text-slate-400 text-xs">未分配</span>
              </template>
            </el-table-column>

            <el-table-column label="系统角色" width="130">
              <template #default="{ row }">
                <el-select 
                  v-model="row.role" 
                  size="small" 
                  :disabled="row.username === 'admin'"
                  @change="(val) => handleRoleChange(row, val)"
                  class="role-select"
                >
                  <el-option label="考生/员工" value="student" />
                  <el-option label="出题人" value="teacher" />
                  <el-option label="超级管理员" value="super_admin" />
                </el-select>
              </template>
            </el-table-column>

            <el-table-column label="账号状态" width="100" align="center">
              <template #default="{ row }">
                <el-switch 
                  v-model="row.is_active" 
                  size="small"
                  :disabled="row.username === 'admin'"
                  @change="(val) => handleStatusChange(row, val)"
                />
              </template>
            </el-table-column>

            <el-table-column label="操作" width="160" align="right">
              <template #default="{ row }">
                <div class="row-actions">
                  <el-button link type="primary" size="small" @click="openEditUserDialog(row)">编辑</el-button>
                  <el-button link type="warning" size="small" @click="removeFromDept(row)" v-if="row.department_id">移出部门</el-button>
                  <el-button link type="danger" size="small" :disabled="row.username === 'admin'" @click="handleDeleteUser(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-footer">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              :total="filteredUsers.length"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 弹窗 1：从 OneAuth 选择同步员工对话框 -->
    <el-dialog
      v-model="candidateDialogVisible"
      title="从 OneAuth 选择导入企业员工"
      width="860px"
      destroy-on-close
    >
      <div class="candidate-dialog-body">
        <!-- 搜索与筛选工具栏 -->
        <div class="candidate-toolbar flex justify-between items-center mb-4 gap-3 flex-wrap">
          <div class="flex items-center gap-3">
            <el-input 
              v-model="candidateKeyword" 
              placeholder="搜索工号、姓名或部门..." 
              clearable 
              style="width: 240px;"
            >
              <template #prefix>
                <Search :size="14" class="text-slate-400" />
              </template>
            </el-input>
            <el-radio-group v-model="candidateFilterType" size="small">
              <el-radio-button label="all">全部 ({{ allCandidates.length }})</el-radio-button>
              <el-radio-button label="unsynced">仅未导入 ({{ unsyncedCount }})</el-radio-button>
              <el-radio-button label="synced">已导入 ({{ syncedCount }})</el-radio-button>
            </el-radio-group>
          </div>

          <el-button size="small" @click="selectUnsyncedAll">
            一键全选未导入成员
          </el-button>
        </div>

        <!-- 候选人多选表格 -->
        <el-table 
          ref="candidateTableRef"
          :data="filteredCandidates" 
          style="width: 100%" 
          height="380px"
          row-key="key"
          @selection-change="handleCandidateSelectionChange"
        >
          <el-table-column type="selection" width="50" align="center" :selectable="canSelectCandidate" />
          
          <el-table-column label="员工信息" min-width="180">
            <template #default="{ row }">
              <div class="flex items-center gap-2">
                <span class="font-bold text-slate-800">{{ row.full_name }}</span>
                <span class="text-xs text-slate-400">({{ row.username }})</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="email" label="企业邮箱" min-width="200" />
          
          <el-table-column prop="dept_name" label="所属 OneAuth 部门" min-width="160">
            <template #default="{ row }">
              <span class="dept-tag-cell">{{ row.dept_name }}</span>
            </template>
          </el-table-column>

          <el-table-column label="同步状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.is_synced" type="success" size="small">已导入</el-tag>
              <el-tag v-else type="primary" size="small" effect="plain">待同步</el-tag>
            </template>
          </el-table-column>
        </el-table>

        <!-- 底部汇总 -->
        <div class="flex justify-between items-center mt-4 pt-3 border-t border-slate-100">
          <div class="text-xs text-slate-500">
            已勾选 <strong class="text-blue-600 text-sm">{{ selectedCandidateKeys.length }}</strong> 位员工
          </div>
          <div class="flex gap-2">
            <el-button @click="candidateDialogVisible = false">取消</el-button>
            <el-button 
              type="primary" 
              :loading="importingUsers" 
              :disabled="!selectedCandidateKeys.length"
              @click="confirmImportCandidates"
            >
              确认导入选中员工 ({{ selectedCandidateKeys.length }})
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 弹窗 2：删除部门确认对话框（支持级联删除或仅删除当前部门） -->
    <el-dialog
      v-model="deleteDeptDialogVisible"
      title="删除部门确认"
      width="480px"
      destroy-on-close
    >
      <div v-if="targetDeptToDelete" class="p-2 text-sm leading-relaxed">
        <div class="flex items-center gap-2 mb-3">
          <AlertTriangle :size="20" class="text-amber-500 flex-shrink-0" />
          <span class="font-bold text-slate-800">确定要删除部门【{{ targetDeptToDelete.name }}】吗？</span>
        </div>

        <div v-if="targetDeptHasChildren" class="p-3 bg-amber-50 rounded-lg text-xs text-amber-900 mb-4 leading-relaxed">
          ⚠️ 该部门下存在 <strong>{{ targetDeptSubCount }} 个子部门</strong>。您可以选择连同所有子部门一并级联删除，或者仅删除当前部门（子部门将保留并自动挂载到上级）。
        </div>
        <div v-else class="text-xs text-slate-500 mb-4">
          该部门下没有子部门。删除后，部门下成员将自动重置为未分配部门。
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2 flex-wrap">
          <el-button @click="deleteDeptDialogVisible = false">取消</el-button>
          <el-button 
            type="danger" 
            plain 
            :loading="deletingDept" 
            @click="executeDeleteDept(false)"
          >
            仅删除当前部门
          </el-button>
          <el-button 
            v-if="targetDeptHasChildren"
            type="danger" 
            :loading="deletingDept" 
            @click="executeDeleteDept(true)"
          >
            连同子部门一起删除 (级联)
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 弹窗 3：新建/编辑部门对话框 -->
    <el-dialog 
      v-model="deptDialogVisible" 
      :title="isEditDept ? '编辑部门名称' : '新建部门'" 
      width="460px"
      destroy-on-close
    >
      <el-form :model="deptForm" label-width="90px">
        <el-form-item label="部门名称" required>
          <el-input v-model="deptForm.name" placeholder="请输入部门名称" />
        </el-form-item>
        <el-form-item label="上级部门">
          <el-tree-select
            v-model="deptForm.parent_id"
            :data="deptTreeData"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            node-key="id"
            value-key="id"
            :render-after-expand="false"
            placeholder="留空为顶级部门"
            clearable
            check-strictly
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deptDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingDept" @click="saveDept">保存</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 4：新建/编辑成员对话框 -->
    <el-dialog 
      v-model="userDialogVisible" 
      :title="isEditUser ? '编辑成员' : '新增成员'" 
      width="540px"
      destroy-on-close
    >
      <el-form :model="userForm" label-width="100px" class="pr-4">
        <el-form-item label="工号/用户名" required>
          <el-input v-model="userForm.username" :disabled="isEditUser" placeholder="例如：zw" />
        </el-form-item>
        <el-form-item label="成员姓名" required>
          <el-input v-model="userForm.full_name" placeholder="例如：zw" />
        </el-form-item>
        <el-form-item label="企业邮箱" required>
          <el-input v-model="userForm.email" placeholder="例如：zw@fit2cloud.com" />
        </el-form-item>
        <el-form-item label="所属部门">
          <el-tree-select
            v-model="userForm.department_id"
            :data="deptTreeData"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            node-key="id"
            value-key="id"
            :render-after-expand="false"
            placeholder="选择所属部门"
            check-strictly
            clearable
          />
        </el-form-item>
        <el-form-item label="系统角色">
          <el-radio-group v-model="userForm.role" :disabled="userForm.username === 'admin'">
            <el-radio label="student">考生/员工</el-radio>
            <el-radio label="teacher">出题人</el-radio>
            <el-radio label="super_admin">超级管理员</el-radio>
          </el-radio-group>
          <div v-if="userForm.username === 'admin'" class="text-xs text-amber-600 mt-1">
            🛡️ 内置管理员 (admin) 角色受系统保护，不可修改为其他角色
          </div>
        </el-form-item>
        <el-form-item label="初始密码" v-if="!isEditUser">
          <el-input v-model="userForm.password" placeholder="默认 123456" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingUser" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- 弹窗 5：身份源配置对话框 -->
    <el-dialog 
      v-model="ssoConfigVisible" 
      title="OneAuth 统一身份源连接配置" 
      width="580px"
      destroy-on-close
    >
      <el-form :model="ssoConfigForm" label-width="120px">
        <el-form-item label="SSO服务地址">
          <el-input v-model="ssoConfigForm.server_url" placeholder="如 http://192.168.123.233:5174" />
        </el-form-item>
        <el-form-item label="同步用户名">
          <el-input v-model="ssoConfigForm.sync_username" placeholder="具有组织只读权限的账号" />
        </el-form-item>
        <el-form-item label="同步密码">
          <el-input v-model="ssoConfigForm.sync_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="Client ID">
          <el-input v-model="ssoConfigForm.client_id" />
        </el-form-item>
        <el-form-item label="Client Secret">
          <el-input v-model="ssoConfigForm.client_secret" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="ssoConfigVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingConfig" @click="saveSSOConfig(false)">保存配置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { userApi } from '@/api'
import { 
  Settings, Building2, UserPlus, RefreshCw, 
  Search, Folder, FolderTree, AlertTriangle,
  ShieldCheck, ChevronDown, Users
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'

// 基础数据
const loading = ref(false)
const syncingDept = ref(false)
const syncingAll = ref(false)
const departments = ref([])
const users = ref([])

// 部门筛选与选中
const selectedDeptId = ref(null)
const deptFilterText = ref('')
const treeRef = ref(null)

// 成员搜索与分页
const userSearchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 成员多选与批量操作
const selectedUsers = ref([])
const userTableRef = ref(null)
const batchRoleLoading = ref(false)

// 部门新建/编辑
const deptDialogVisible = ref(false)
const isEditDept = ref(false)
const editDeptId = ref(null)
const savingDept = ref(false)
const deptForm = ref({ name: '', parent_id: null })

// 删除部门专用对话框
const deleteDeptDialogVisible = ref(false)
const targetDeptToDelete = ref(null)
const deletingDept = ref(false)

// 成员新建/编辑
const userDialogVisible = ref(false)
const isEditUser = ref(false)
const editUserId = ref(null)
const savingUser = ref(false)
const userForm = ref({
  username: '',
  full_name: '',
  email: '',
  role: 'student',
  department_id: null,
  is_active: true,
  password: '123456'
})

// SSO 配置
const ssoConfigVisible = ref(false)
const savingConfig = ref(false)
const ssoConfigForm = ref({
  server_url: '',
  sync_username: '',
  sync_password: '',
  client_id: '',
  client_secret: ''
})

// 候选员工选择导入
const candidateDialogVisible = ref(false)
const loadingCandidates = ref(false)
const importingUsers = ref(false)
const allCandidates = ref([])
const candidateKeyword = ref('')
const candidateFilterType = ref('all')
const selectedCandidateKeys = ref([])
const candidateTableRef = ref(null)

// 加载全部数据
const fetchAll = async () => {
  loading.value = true
  try {
    const [deptRes, userRes] = await Promise.all([
      userApi.getDepartments(),
      userApi.getUsers()
    ])
    departments.value = deptRes
    users.value = userRes
  } finally {
    loading.value = false
  }
}

// 部门树形构建
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

// 部门树过滤
watch(deptFilterText, (val) => {
  treeRef.value?.filter(val)
})

const filterNode = (value, data) => {
  if (!value) return true
  return data.name.toLowerCase().includes(value.toLowerCase())
}

const handleTreeNodeClick = (data) => {
  selectedDeptId.value = data.id
  currentPage.value = 1
}

const selectDept = (deptId) => {
  selectedDeptId.value = deptId
  currentPage.value = 1
}

const selectedDeptName = computed(() => {
  if (!selectedDeptId.value) return null
  const d = departments.value.find(item => item.id === selectedDeptId.value)
  return d ? d.name : null
})

// 递归收集该部门以及所有子部门 ID
const collectSubtreeIds = (deptId) => {
  const ids = [deptId]
  const findChildren = (pid) => {
    departments.value.forEach(d => {
      if (d.parent_id === pid) {
        ids.push(d.id)
        findChildren(d.id)
      }
    })
  }
  findChildren(deptId)
  return ids
}

// 过滤用户列表
const filteredUsers = computed(() => {
  let list = users.value

  if (selectedDeptId.value) {
    const allowedDeptIds = collectSubtreeIds(selectedDeptId.value)
    list = list.filter(u => u.department_id && allowedDeptIds.includes(u.department_id))
  }

  if (userSearchKeyword.value.trim()) {
    const kw = userSearchKeyword.value.trim().toLowerCase()
    list = list.filter(u => 
      (u.full_name && u.full_name.toLowerCase().includes(kw)) ||
      (u.username && u.username.toLowerCase().includes(kw)) ||
      (u.email && u.email.toLowerCase().includes(kw))
    )
  }

  return list
})

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredUsers.value.slice(start, start + pageSize.value)
})

// 部门操作
const openCreateDeptDialog = (parentId = null) => {
  isEditDept.value = false
  editDeptId.value = null
  deptForm.value = {
    name: '',
    parent_id: parentId
  }
  deptDialogVisible.value = true
}

const targetDeptSubCount = computed(() => {
  if (!targetDeptToDelete.value) return 0
  const subIds = collectSubtreeIds(targetDeptToDelete.value.id)
  return Math.max(0, subIds.length - 1)
})

const targetDeptHasChildren = computed(() => targetDeptSubCount.value > 0)

const handleDeptCommand = (command, data) => {
  if (command === 'addChild') {
    openCreateDeptDialog(data.id)
  } else if (command === 'edit') {
    isEditDept.value = true
    editDeptId.value = data.id
    deptForm.value = {
      name: data.name,
      parent_id: data.parent_id
    }
    deptDialogVisible.value = true
  } else if (command === 'delete') {
    targetDeptToDelete.value = data
    deleteDeptDialogVisible.value = true
  }
}

const executeDeleteDept = async (cascade = false) => {
  if (!targetDeptToDelete.value) return
  deletingDept.value = true
  try {
    const res = await userApi.deleteDepartment(targetDeptToDelete.value.id, { cascade })
    ElMessage.success(res.message || '部门已成功删除')
    if (selectedDeptId.value === targetDeptToDelete.value.id) {
      selectedDeptId.value = null
    }
    deleteDeptDialogVisible.value = false
    fetchAll()
  } catch (e) {
    // 错误在拦截器已提示
  } finally {
    deletingDept.value = false
  }
}

const saveDept = async () => {
  if (!deptForm.value.name) {
    ElMessage.warning('请输入部门名称')
    return
  }
  savingDept.value = true
  try {
    if (isEditDept.value) {
      await userApi.updateDepartment(editDeptId.value, deptForm.value)
      ElMessage.success('部门更新成功')
    } else {
      await userApi.createDepartment(deptForm.value)
      ElMessage.success('部门创建成功')
    }
    deptDialogVisible.value = false
    fetchAll()
  } finally {
    savingDept.value = false
  }
}

// 成员操作
const openCreateUserDialog = () => {
  isEditUser.value = false
  editUserId.value = null
  userForm.value = {
    username: '',
    full_name: '',
    email: '',
    role: 'student',
    department_id: selectedDeptId.value || null,
    is_active: true,
    password: '123456'
  }
  userDialogVisible.value = true
}

const openEditUserDialog = (row) => {
  isEditUser.value = true
  editUserId.value = row.id
  userForm.value = {
    username: row.username,
    full_name: row.full_name,
    email: row.email,
    role: row.role,
    department_id: row.department_id,
    is_active: row.is_active,
    password: ''
  }
  userDialogVisible.value = true
}

const saveUser = async () => {
  if (!userForm.value.username || !userForm.value.full_name) {
    ElMessage.warning('请填写工号和成员姓名')
    return
  }
  savingUser.value = true
  try {
    if (isEditUser.value) {
      await userApi.updateUser(editUserId.value, userForm.value)
      ElMessage.success('成员信息更新成功')
    } else {
      await userApi.createUser(userForm.value)
      ElMessage.success('成员新增成功')
    }
    userDialogVisible.value = false
    fetchAll()
  } finally {
    savingUser.value = false
  }
}

const handleRoleChange = async (row, newRole) => {
  try {
    await userApi.updateUser(row.id, { role: newRole })
    ElMessage.success(`已将【${row.full_name}】角色变更为 ${getRoleText(newRole)}`)
  } catch (e) {
    fetchAll()
  }
}

// 成员表格多选处理
const handleUserSelectionChange = (selection) => {
  selectedUsers.value = selection
}

const clearUserSelection = () => {
  userTableRef.value?.clearSelection()
  selectedUsers.value = []
}

// 批量修改所选成员角色
const handleBatchRoleChange = (role) => {
  if (!selectedUsers.value.length) return
  const roleName = getRoleText(role)
  const userIds = selectedUsers.value.map(u => u.id)
  const count = userIds.length

  ElMessageBox.confirm(
    `确定要将已选中的 ${count} 位成员的角色批量修改为【${roleName}】吗？`,
    '批量修改角色确认',
    {
      confirmButtonText: '确定修改',
      cancelButtonText: '取消',
      type: role === 'super_admin' ? 'warning' : 'info'
    }
  ).then(async () => {
    batchRoleLoading.value = true
    try {
      const res = await userApi.batchUpdateUserRole({
        user_ids: userIds,
        role: role
      })
      ElMessage.success(res.message || `已成功将 ${count} 位成员角色修改为 ${roleName}`)
      clearUserSelection()
      await fetchAll()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '批量修改角色失败')
    } finally {
      batchRoleLoading.value = false
    }
  }).catch(() => {})
}

const handleStatusChange = async (row, newStatus) => {
  try {
    await userApi.updateUser(row.id, { is_active: newStatus })
    ElMessage.success(`账号状态已更新`)
  } catch (e) {
    fetchAll()
  }
}

const removeFromDept = (row) => {
  ElMessageBox.confirm(`确定将【${row.full_name}】移出当前部门吗？`, '移出部门确认').then(async () => {
    await userApi.updateUser(row.id, { department_id: null })
    ElMessage.success('已移出部门')
    fetchAll()
  })
}

const handleDeleteUser = (row) => {
  ElMessageBox.confirm(`确定要删除成员【${row.full_name}】吗？`, '删除确认', {
    type: 'warning'
  }).then(async () => {
    await userApi.deleteUser(row.id)
    ElMessage.success('成员已删除')
    fetchAll()
  })
}

// 仅同步部门（幂等：已存在跳过）
const handleSyncDepartmentsOnly = async () => {
  syncingDept.value = true
  try {
    const res = await userApi.syncDepartments()
    ElMessage.success(res.message || '部门架构同步完成')
    fetchAll()
  } catch (e) {
    ElMessage.error('同步部门失败')
  } finally {
    syncingDept.value = false
  }
}

// 打开选择同步员工弹窗
const openCandidateUsersDialog = async () => {
  loadingCandidates.value = true
  try {
    const res = await userApi.getOneAuthCandidates()
    allCandidates.value = res.data || []
    selectedCandidateKeys.value = []
    candidateFilterType.value = 'all'
    candidateKeyword.value = ''
    candidateDialogVisible.value = true
  } catch (e) {
    ElMessage.error('获取 OneAuth 成员候选列表失败')
  } finally {
    loadingCandidates.value = false
  }
}

// 候选人员统计
const syncedCount = computed(() => allCandidates.value.filter(c => c.is_synced).length)
const unsyncedCount = computed(() => allCandidates.value.filter(c => !c.is_synced).length)

const filteredCandidates = computed(() => {
  let list = allCandidates.value
  if (candidateFilterType.value === 'unsynced') {
    list = list.filter(c => !c.is_synced)
  } else if (candidateFilterType.value === 'synced') {
    list = list.filter(c => c.is_synced)
  }

  if (candidateKeyword.value.trim()) {
    const kw = candidateKeyword.value.trim().toLowerCase()
    list = list.filter(c => 
      c.username.toLowerCase().includes(kw) ||
      c.full_name.toLowerCase().includes(kw) ||
      (c.dept_name && c.dept_name.toLowerCase().includes(kw)) ||
      (c.email && c.email.toLowerCase().includes(kw))
    )
  }
  return list
})

const canSelectCandidate = () => true

const handleCandidateSelectionChange = (selection) => {
  selectedCandidateKeys.value = selection.map(item => item.key)
}

const selectUnsyncedAll = () => {
  const unsyncedRows = filteredCandidates.value.filter(c => !c.is_synced)
  if (candidateTableRef.value) {
    unsyncedRows.forEach(row => {
      candidateTableRef.value.toggleRowSelection(row, true)
    })
  }
}

const confirmImportCandidates = async () => {
  if (!selectedCandidateKeys.value.length) {
    ElMessage.warning('请至少勾选一位要导入的员工')
    return
  }
  importingUsers.value = true
  try {
    const res = await userApi.importOneAuthUsers(selectedCandidateKeys.value)
    ElMessage.success(res.message || `成功导入 ${selectedCandidateKeys.value.length} 位员工`)
    candidateDialogVisible.value = false
    fetchAll()
  } catch (e) {
    ElMessage.error('导入员工失败')
  } finally {
    importingUsers.value = false
  }
}

// 一键全量同步
const handleSyncAllData = async () => {
  syncingAll.value = true
  try {
    const res = await userApi.syncOneAuth()
    ElMessage.success(res.message || '全量架构与员工同步完成')
    fetchAll()
  } catch (e) {
    ElMessage.error('同步失败')
  } finally {
    syncingAll.value = false
  }
}

// 打开 SSO 配置
const openSSOConfigDialog = async () => {
  try {
    const cfg = await userApi.getSSOConfig()
    ssoConfigForm.value = { ...cfg }
    ssoConfigVisible.value = true
  } catch (e) {
    ElMessage.error('获取配置失败')
  }
}

const saveSSOConfig = async (triggerSync = false) => {
  if (!ssoConfigForm.value.server_url) {
    ElMessage.warning('请输入身份源服务地址')
    return
  }
  savingConfig.value = true
  try {
    await userApi.updateSSOConfig(ssoConfigForm.value)
    ElMessage.success('身份源连接配置已保存')
    ssoConfigVisible.value = false
    if (triggerSync) {
      handleSyncAllData()
    }
  } finally {
    savingConfig.value = false
  }
}

const getRoleText = (role) => {
  if (role === 'super_admin') return '超级管理员'
  if (role === 'teacher') return '出题人'
  return '考生/员工'
}

const getAvatarText = (name) => {
  if (!name) return '员'
  if (name.length <= 2) return name
  return name.slice(0, 2)
}

const colors = [
  '#3b82f6', '#8b5cf6', '#10b981', '#06b6d4', 
  '#f59e0b', '#ec4899', '#6366f1', '#14b8a6'
]
const getAvatarColor = (name) => {
  if (!name) return colors[0]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % colors.length
  return colors[index]
}

onMounted(() => {
  fetchAll()
})
</script>

<style scoped>
.org-manage-page {
  max-width: 1360px;
  margin: 0 auto;
}

.top-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.page-subtitle {
  font-size: 12px;
  color: #64748b;
  margin: 4px 0 0 0;
}

.btn-icon {
  margin-right: 5px;
}

.org-layout-grid {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 20px;
  align-items: start;
}
@media (max-width: 900px) {
  .org-layout-grid {
    grid-template-columns: 1fr;
  }
}

/* 部门树卡片：设置 sticky 锁定在视口顶部，不随右侧成员长表格滚动走 */
.dept-tree-card {
  padding: 16px;
  background: white;
  border-radius: 12px;
  position: sticky;
  top: 0;
  align-self: start;
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}
.dept-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.tree-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.tree-subtitle {
  font-size: 11px;
  color: #94a3b8;
  margin: 2px 0 0 0;
}
.dept-search-wrap {
  margin-bottom: 12px;
  flex-shrink: 0;
}

.dept-tree-body {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.all-dept-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 6px;
  font-size: 13px;
  transition: all 0.15s;
}
.all-dept-item:hover {
  background: #f1f5f9;
}
.all-dept-item.is-selected {
  background: #eff6ff;
  color: #2563eb;
}
.dept-count-badge {
  font-size: 11px;
  background: #e2e8f0;
  color: #475569;
  padding: 1px 6px;
  border-radius: 10px;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 4px;
  font-size: 13px;
}
.node-left {
  display: flex;
  align-items: center;
  gap: 6px;
}
.dept-icon {
  color: #94a3b8;
}
.more-dot {
  color: #94a3b8;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
}
.more-dot:hover {
  background: #e2e8f0;
}

/* 成员卡片 */
.dept-members-card {
  padding: 20px;
  background: white;
  border-radius: 12px;
}
.members-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}
.header-title-box {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.members-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.members-count {
  font-size: 12px;
  color: #94a3b8;
}
.header-action-box {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-search-input {
  width: 220px;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar-cell {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}
.user-meta-wrap {
  display: flex;
  flex-direction: column;
}
.user-name-line {
  display: flex;
  align-items: center;
  gap: 6px;
}
.full-name {
  font-weight: 600;
  color: #1e293b;
  font-size: 13px;
}
.user-email-text {
  font-size: 11px;
  color: #94a3b8;
}
.dept-tag-cell {
  background: #f1f5f9;
  color: #475569;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
}

.role-select {
  width: 115px;
}
.row-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

.pagination-footer {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 批量操作工具条 */
.batch-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 100%);
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 14px;
  box-shadow: 0 2px 6px rgba(37, 99, 235, 0.06);
}
.batch-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.batch-badge {
  font-size: 13px;
  color: #1e40af;
  font-weight: 500;
}
.batch-badge strong {
  font-weight: 700;
  color: #2563eb;
  font-size: 15px;
}
.batch-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 批量角色选择项 */
.batch-role-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 2px;
}
.role-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.role-dot.student {
  background-color: #64748b;
}
.role-dot.teacher {
  background-color: #d97706;
}
.role-dot.admin {
  background-color: #e11d48;
}
.role-item-title {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}
.role-item-desc {
  font-size: 11px;
  color: #94a3b8;
}
</style>
