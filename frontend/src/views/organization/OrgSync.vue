<template>
  <AppPage class="org-manage-page">
    <AppPageHeader
      eyebrow="系统与集成"
      title="组织架构与成员管理"
      description="统一管理企业部门层级、员工名册与 OneAuth 身份源数据实时对齐"
    >
      <template #actions>
        <a-button @click="openSSOConfigDialog">
          <Settings :size="14" class="btn-icon" /> 身份源配置
        </a-button>
        <a-button type="outline" :loading="syncingDept" @click="handleSyncDepartmentsOnly">
          <Building2 :size="14" class="btn-icon" /> 同步部门架构
        </a-button>
        <a-button type="primary" :loading="loadingCandidates" @click="openCandidateUsersDialog">
          <UserPlus :size="14" class="btn-icon" /> 选择同步 OneAuth 成员
        </a-button>
        <a-button type="outline" status="success" :loading="syncingAll" @click="handleSyncAllData">
          <RefreshCw :size="14" class="btn-icon" /> 一键全量同步
        </a-button>
      </template>
    </AppPageHeader>

    <!-- 主体两栏布局：左侧部门树 + 右侧成员列表 -->
    <div class="org-layout-grid">
      <!-- 左栏：组织架构树卡片 (设置 sticky 保持视口固定不滑移) -->
      <div class="dept-tree-card app-card">
        <div class="dept-card-header">
          <div>
            <h3 class="tree-title">组织架构</h3>
            <p class="tree-subtitle">部门层级与关联</p>
          </div>
          <a-button type="primary" size="small" class="new-dept-btn" @click="openCreateDeptDialog(null)">
            + 新建部门
          </a-button>
        </div>

        <!-- 部门搜索框 -->
        <div class="dept-search-wrap">
          <a-input
            v-model="deptFilterText"
            placeholder="搜索部门名称"
            allow-clear
            size="default"
          >
            <template #prefix>
              <Search :size="14" class="text-slate-400" />
            </template>
          </a-input>
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

          <a-tree
            :data="filteredDeptTreeData"
            :field-names="{ title: 'name', key: 'id', children: 'children' }"
            v-model:expanded-keys="expandedDeptKeys"
            block-node
            @select="handleTreeSelect"
          >
            <template #title="data">
              <div class="custom-tree-node">
                <div class="node-left">
                  <FolderTree :size="14" class="dept-icon" />
                  <span class="node-label">{{ data.name }}</span>
                </div>

                <div class="node-actions" @click.stop>
                  <a-dropdown trigger="click" @select="(cmd) => handleDeptCommand(cmd, data)">
                    <span class="more-dot">•••</span>
                    <template #content>
                      <a-doption value="addChild">+ 添加子部门</a-doption>
                      <a-doption value="edit">编辑名称</a-doption>
                      <a-doption value="delete" class="text-red-500">删除部门...</a-doption>
                    </template>
                  </a-dropdown>
                </div>
              </div>
            </template>
          </a-tree>
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
            <a-input
              v-model="userSearchKeyword"
              placeholder="按成员姓名或邮箱搜索"
              allow-clear
              class="user-search-input"
            >
              <template #prefix>
                <Search :size="14" class="text-slate-400" />
              </template>
            </a-input>

            <a-button type="primary" @click="openCreateUserDialog">
              + 添加成员
            </a-button>
          </div>
        </div>

        <!-- 批量操作栏（多选成员时显示） -->
        <transition name="fade">
          <div v-if="selectedUsers.length > 0" class="batch-bar">
            <div class="batch-left">
              <span class="batch-badge">
                已选中 <strong>{{ selectedUsers.length }}</strong> 位成员
              </span>
            </div>
            <div class="batch-right">
              <a-dropdown trigger="click" @select="handleBatchRoleChange">
                <a-button type="primary" :loading="batchRoleLoading">
                  <ShieldCheck :size="15" class="mr-1.5" />
                  批量设置角色
                  <ChevronDown :size="14" class="ml-1" />
                </a-button>
                <template #content>
                    <a-doption value="student">
                      <div class="batch-role-item">
                        <span class="role-dot student"></span>
                        <div>
                          <div class="role-item-title">考生 / 普通员工</div>
                          <div class="role-item-desc">仅参加考试与查卷 (student)</div>
                        </div>
                      </div>
                    </a-doption>
                    <a-doption value="teacher">
                      <div class="batch-role-item">
                        <span class="role-dot teacher"></span>
                        <div>
                          <div class="role-item-title text-amber-600">出题人 / 阅卷老师</div>
                          <div class="role-item-desc">试卷题库与阅卷考务 (teacher)</div>
                        </div>
                      </div>
                    </a-doption>
                    <a-doption value="super_admin">
                      <div class="batch-role-item">
                        <span class="role-dot admin"></span>
                        <div>
                          <div class="role-item-title text-rose-600">超级管理员</div>
                          <div class="role-item-desc">全系统配置与管理权限 (super_admin)</div>
                        </div>
                      </div>
                    </a-doption>
                </template>
              </a-dropdown>

              <a-button type="outline" status="danger" :loading="batchDeleteLoading" @click="handleBatchDeleteUsers">
                <Trash2 :size="15" class="mr-1.5" />
                批量删除
              </a-button>

              <a-button @click="clearUserSelection">
                取消选择
              </a-button>
            </div>
          </div>
        </transition>

        <!-- 成员表格 -->
        <div class="table-container">
          <a-table
            :columns="userColumns"
            :data="paginatedUsers"
            :loading="loading"
            :pagination="false"
            :row-selection="{ type: 'checkbox', showCheckedAll: true }"
            v-model:selected-keys="selectedUserKeys"
            row-key="id"
            class="custom-table"
            @selection-change="handleUserSelectionChange"
          >
            <template #member="{ record: row }">
                <div class="user-cell">
                  <div class="avatar-cell" :style="{ backgroundColor: getAvatarColor(row.full_name) }">
                    {{ getAvatarText(row.full_name) }}
                  </div>
                  <div class="user-meta-wrap">
                    <div class="user-name-line">
                      <span class="full-name">{{ row.full_name }}</span>
                      <a-tag v-if="row.role === 'super_admin'" color="red" size="small">超管</a-tag>
                      <a-tag v-else-if="row.role === 'teacher'" color="orange" size="small">出题人</a-tag>
                    </div>
                    <span class="user-email-text">{{ row.email || row.username }}</span>
                  </div>
                </div>
            </template>
            <template #department="{ record: row }">
                <span v-if="row.department_name" class="dept-tag-cell">{{ row.department_name }}</span>
                <span v-else class="text-slate-400 text-xs">未分配</span>
            </template>
            <template #role="{ record: row }">
                <a-select
                  v-model="row.role"
                  size="small"
                  :disabled="row.username === 'admin'"
                  @change="(val) => handleRoleChange(row, val)"
                  class="role-select"
                >
                  <a-option label="考生/员工" value="student" />
                  <a-option label="出题人" value="teacher" />
                  <a-option label="超级管理员" value="super_admin" />
                </a-select>
            </template>
            <template #status="{ record: row }">
                <a-switch
                  v-model="row.is_active"
                  size="small"
                  :disabled="row.username === 'admin'"
                  @change="(val) => handleStatusChange(row, val)"
                />
            </template>
            <template #actions="{ record: row }">
                <div class="row-actions">
                  <a-button type="text" size="mini" @click="openEditUserDialog(row)">编辑</a-button>
                  <a-button v-if="row.department_id" type="text" status="warning" size="mini" @click="removeFromDept(row)">移出部门</a-button>
                  <a-button type="text" status="danger" size="mini" :disabled="row.username === 'admin'" @click="handleDeleteUser(row)">删除</a-button>
                </div>
            </template>
          </a-table>

          <!-- 分页 -->
          <div class="pagination-footer">
            <a-pagination
              :current="currentPage"
              :page-size="pageSize"
              :page-size-options="[10, 20, 50, 100]"
              show-total
              show-page-size
              :total="filteredUsers.length"
              @change="handlePageChange"
              @page-size-change="handlePageSizeChange"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 弹窗 1：从 OneAuth 选择同步员工对话框 -->
    <a-modal
      v-model:visible="candidateDialogVisible"
      title="从 OneAuth 选择导入企业员工"
      width="840px"
      unmount-on-close
      :footer="false"
    >
      <div class="candidate-dialog-body">
        <!-- 搜索与筛选工具栏 -->
        <div class="candidate-toolbar flex justify-between items-center mb-4 gap-3 flex-wrap">
          <div class="flex items-center gap-3">
            <a-input
              v-model="candidateKeyword"
              placeholder="搜索工号、姓名或部门..."
              allow-clear
              style="width: 240px;"
            >
              <template #prefix>
                <Search :size="14" class="text-slate-400" />
              </template>
            </a-input>
            <a-radio-group v-model="candidateFilterType" size="small">
              <a-radio value="all">全部 ({{ allCandidates.length }})</a-radio>
              <a-radio value="unsynced">仅未导入 ({{ unsyncedCount }})</a-radio>
              <a-radio value="synced">已导入 ({{ syncedCount }})</a-radio>
            </a-radio-group>
          </div>

          <a-button size="small" @click="selectUnsyncedAll">
            一键全选未导入成员
          </a-button>
        </div>

        <!-- 候选人多选表格 -->
        <a-table
          :columns="candidateColumns"
          :data="filteredCandidates"
          :pagination="false"
          :scroll="{ y: 380 }"
          :row-selection="{ type: 'checkbox', showCheckedAll: true }"
          v-model:selected-keys="selectedCandidateKeys"
          row-key="key"
        >
          <template #candidate="{ record: row }">
              <div class="flex items-center gap-2">
                <span class="font-bold text-slate-800">{{ row.full_name }}</span>
                <span class="text-xs text-slate-400">({{ row.username }})</span>
              </div>
          </template>
          <template #department="{ record: row }">
            <span class="dept-tag-cell">{{ row.dept_name }}</span>
          </template>
          <template #syncStatus="{ record: row }">
            <a-tag v-if="row.is_synced" color="green" size="small">已导入</a-tag>
            <a-tag v-else color="blue" size="small">待同步</a-tag>
          </template>
        </a-table>

        <!-- 底部汇总 -->
        <div class="flex justify-between items-center mt-4 pt-3 border-t border-slate-100">
          <div class="text-xs text-slate-500">
            已勾选 <strong class="text-blue-600 text-sm">{{ selectedCandidateKeys.length }}</strong> 位员工
          </div>
          <div class="flex gap-2">
            <a-button @click="candidateDialogVisible = false">取消</a-button>
            <a-button
              type="primary"
              :loading="importingUsers"
              :disabled="!selectedCandidateKeys.length"
              @click="confirmImportCandidates"
            >
              确认导入选中员工 ({{ selectedCandidateKeys.length }})
            </a-button>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 弹窗 2：删除部门确认对话框（支持级联删除或仅删除当前部门） -->
    <a-modal
      v-model:visible="deleteDeptDialogVisible"
      title="删除部门确认"
      width="480px"
      unmount-on-close
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
          <a-button @click="deleteDeptDialogVisible = false">取消</a-button>
          <a-button
            type="outline"
            status="danger"
            :loading="deletingDept"
            @click="executeDeleteDept(false)"
          >
            仅删除当前部门
          </a-button>
          <a-button
            v-if="targetDeptHasChildren"
            type="primary"
            status="danger"
            :loading="deletingDept"
            @click="executeDeleteDept(true)"
          >
            连同子部门一起删除 (级联)
          </a-button>
        </div>
      </template>
    </a-modal>

    <!-- 弹窗 3：新建/编辑部门对话框 -->
    <a-modal
      v-model:visible="deptDialogVisible"
      :title="isEditDept ? '编辑部门名称' : '新建部门'"
      width="480px"
      unmount-on-close
    >
      <a-form :model="deptForm" :label-col-props="{ span: 6 }" :wrapper-col-props="{ span: 18 }">
        <a-form-item label="部门名称" required>
          <a-input v-model="deptForm.name" placeholder="请输入部门名称" />
        </a-form-item>
        <a-form-item label="上级部门">
          <a-tree-select
            v-model="deptForm.parent_id"
            :data="deptTreeData"
            :field-names="{ title: 'name', key: 'id', children: 'children' }"
            placeholder="留空为顶级部门"
            allow-clear
          />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="deptDialogVisible = false">取消</a-button>
        <a-button type="primary" :loading="savingDept" @click="saveDept">保存</a-button>
      </template>
    </a-modal>

    <!-- 弹窗 4：新建/编辑成员对话框 -->
    <a-modal
      v-model:visible="userDialogVisible"
      :title="isEditUser ? '编辑成员' : '新增成员'"
      width="640px"
      unmount-on-close
    >
      <a-form :model="userForm" :label-col-props="{ span: 6 }" :wrapper-col-props="{ span: 18 }" class="pr-4">
        <a-form-item label="工号/用户名" required>
          <a-input v-model="userForm.username" :disabled="isEditUser" placeholder="例如：zw" />
        </a-form-item>
        <a-form-item label="成员姓名" required>
          <a-input v-model="userForm.full_name" placeholder="例如：zw" />
        </a-form-item>
        <a-form-item label="企业邮箱" required>
          <a-input v-model="userForm.email" placeholder="例如：zw@fit2cloud.com" />
        </a-form-item>
        <a-form-item label="所属部门">
          <a-tree-select
            v-model="userForm.department_id"
            :data="deptTreeData"
            :field-names="{ title: 'name', key: 'id', children: 'children' }"
            placeholder="选择所属部门"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="系统角色">
          <a-radio-group v-model="userForm.role" :disabled="userForm.username === 'admin'">
            <a-radio value="student">考生/员工</a-radio>
            <a-radio value="teacher">出题人</a-radio>
            <a-radio value="super_admin">超级管理员</a-radio>
          </a-radio-group>
          <div v-if="userForm.username === 'admin'" class="text-xs text-amber-600 mt-1">
            🛡️ 内置管理员 (admin) 角色受系统保护，不可修改为其他角色
          </div>
        </a-form-item>
        <a-form-item label="初始密码" v-if="!isEditUser">
          <a-input-password v-model="userForm.password" placeholder="默认 123456" allow-clear />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="userDialogVisible = false">取消</a-button>
        <a-button type="primary" :loading="savingUser" @click="saveUser">保存</a-button>
      </template>
    </a-modal>

    <!-- 弹窗 5：身份源配置对话框 -->
    <a-modal
      v-model:visible="ssoConfigVisible"
      title="OneAuth 统一身份源连接配置"
      width="640px"
      unmount-on-close
    >
      <a-form :model="ssoConfigForm" :label-col-props="{ span: 6 }" :wrapper-col-props="{ span: 18 }">
        <a-form-item label="SSO服务地址">
          <a-input v-model="ssoConfigForm.server_url" placeholder="如 http://192.168.123.233:5174" />
        </a-form-item>
        <a-form-item label="Client ID">
          <a-input v-model="ssoConfigForm.client_id" placeholder="如 app_52a0a477a52301c3" />
        </a-form-item>
        <a-form-item label="Client Secret">
          <a-input-password v-model="ssoConfigForm.client_secret" allow-clear placeholder="OneAuth 分配的 Client Secret" />
        </a-form-item>
        <a-form-item label="授权回调地址">
          <a-input v-model="ssoConfigForm.redirect_uri" :placeholder="currentAutoRedirectUri" />
          <div class="text-xs text-slate-400 mt-1">
            智能默认：<span class="text-blue-600 font-mono">{{ currentAutoRedirectUri }}</span>（请确保在 OneAuth 登录控制台中登记此回调地址）
          </div>
        </a-form-item>

        <a-divider orientation="left"><span class="text-xs text-slate-400">组织架构与员工同步账号 (可选)</span></a-divider>
        <a-form-item label="同步用户名">
          <a-input v-model="ssoConfigForm.sync_username" placeholder="具有组织只读权限的账号" />
        </a-form-item>
        <a-form-item label="同步密码">
          <a-input-password v-model="ssoConfigForm.sync_password" allow-clear />
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button type="outline" status="success" :loading="testingConfig" @click="testSSOConfig">测试连接</a-button>
        <a-button @click="ssoConfigVisible = false">取消</a-button>
        <a-button type="primary" :loading="savingConfig" @click="saveSSOConfig(false)">保存配置</a-button>
      </template>
    </a-modal>
  </AppPage>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { userApi } from '@/api'
import {
  Settings, Building2, UserPlus, RefreshCw,
  Search, Folder, FolderTree, AlertTriangle,
  ShieldCheck, ChevronDown, Trash2
} from 'lucide-vue-next'
import { Message, Modal } from '@arco-design/web-vue'
import AppPage from '@/components/ui/AppPage.vue'
import AppPageHeader from '@/components/ui/AppPageHeader.vue'

const userColumns = [
  { title: '成员信息', minWidth: 220, slotName: 'member' },
  { title: '工号/用户名', dataIndex: 'username', minWidth: 130 },
  { title: '所属部门', minWidth: 140, slotName: 'department' },
  { title: '系统角色', width: 130, slotName: 'role' },
  { title: '账号状态', width: 100, align: 'center', slotName: 'status' },
  { title: '操作', width: 190, align: 'right', slotName: 'actions' }
]

const candidateColumns = [
  { title: '员工信息', minWidth: 180, slotName: 'candidate' },
  { title: '企业邮箱', dataIndex: 'email', minWidth: 200 },
  { title: '所属 OneAuth 部门', minWidth: 160, slotName: 'department' },
  { title: '同步状态', width: 110, align: 'center', slotName: 'syncStatus' }
]

// 基础数据
const loading = ref(false)
const syncingDept = ref(false)
const syncingAll = ref(false)
const departments = ref([])
const users = ref([])

// 部门筛选与选中
const selectedDeptId = ref(null)
const deptFilterText = ref('')
const expandedDeptKeys = ref([])

// 成员搜索与分页
const userSearchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 成员多选与批量操作
const selectedUsers = ref([])
const selectedUserKeys = ref([])
const batchRoleLoading = ref(false)
const batchDeleteLoading = ref(false)

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
const testingConfig = ref(false)
const currentAutoRedirectUri = computed(() => {
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/auth/callback`
  }
  return ''
})
const ssoConfigForm = ref({
  server_url: '',
  sync_username: '',
  sync_password: '',
  client_id: '',
  client_secret: '',
  redirect_uri: ''
})

// 候选员工选择导入
const candidateDialogVisible = ref(false)
const loadingCandidates = ref(false)
const importingUsers = ref(false)
const allCandidates = ref([])
const candidateKeyword = ref('')
const candidateFilterType = ref('all')
const selectedCandidateKeys = ref([])

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

watch(deptTreeData, (tree) => {
  const keys = []
  const collectKeys = (nodes) => nodes.forEach(node => {
    keys.push(node.id)
    collectKeys(node.children || [])
  })
  collectKeys(tree)
  expandedDeptKeys.value = keys
}, { immediate: true })

// 搜索时保留命中的部门及其上级路径，避免打散原有层级。
const filteredDeptTreeData = computed(() => {
  const keyword = deptFilterText.value.trim().toLowerCase()
  if (!keyword) return deptTreeData.value
  const filterNodes = (nodes) => nodes.reduce((result, node) => {
    const children = filterNodes(node.children || [])
    if (node.name.toLowerCase().includes(keyword) || children.length) {
      result.push({ ...node, children })
    }
    return result
  }, [])
  return filterNodes(deptTreeData.value)
})

const handleTreeSelect = (_selectedKeys, event) => {
  const data = event?.selectedNodes?.[0] || event?.node
  if (!data) return
  selectedDeptId.value = data.id || data.key
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

const handlePageChange = (page) => {
  currentPage.value = page
}

const handlePageSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

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
    Message.success(res.message || '部门已成功删除')
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
    Message.warning('请输入部门名称')
    return
  }
  savingDept.value = true
  try {
    if (isEditDept.value) {
      await userApi.updateDepartment(editDeptId.value, deptForm.value)
      Message.success('部门更新成功')
    } else {
      await userApi.createDepartment(deptForm.value)
      Message.success('部门创建成功')
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
    Message.warning('请填写工号和成员姓名')
    return
  }
  savingUser.value = true
  try {
    if (isEditUser.value) {
      await userApi.updateUser(editUserId.value, userForm.value)
      Message.success('成员信息更新成功')
    } else {
      await userApi.createUser(userForm.value)
      Message.success('成员新增成功')
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
    Message.success(`已将【${row.full_name}】角色变更为 ${getRoleText(newRole)}`)
  } catch (e) {
    fetchAll()
  }
}

// 成员表格多选处理
const handleUserSelectionChange = (keys) => {
  selectedUserKeys.value = keys
  selectedUsers.value = users.value.filter(user => keys.includes(user.id))
}

const clearUserSelection = () => {
  selectedUserKeys.value = []
  selectedUsers.value = []
}

// 批量修改所选成员角色
const handleBatchRoleChange = (role) => {
  if (!selectedUsers.value.length) return
  const roleName = getRoleText(role)
  const userIds = selectedUsers.value.map(u => u.id)
  const count = userIds.length

  Modal.confirm({
    title: '批量修改角色确认',
    content: `确定要将已选中的 ${count} 位成员的角色批量修改为【${roleName}】吗？`,
    okText: '确定修改',
    cancelText: '取消',
    simple: false,
    onOk: async () => {
      batchRoleLoading.value = true
      try {
        const res = await userApi.batchUpdateUserRole({ user_ids: userIds, role })
        Message.success(res.message || `已成功将 ${count} 位成员角色修改为 ${roleName}`)
        clearUserSelection()
        await fetchAll()
      } catch (e) {
        Message.error(e.response?.data?.detail || '批量修改角色失败')
        return false
      } finally {
        batchRoleLoading.value = false
      }
    }
  })
}

const handleStatusChange = async (row, newStatus) => {
  try {
    await userApi.updateUser(row.id, { is_active: newStatus })
    Message.success(`账号状态已更新`)
  } catch (e) {
    fetchAll()
  }
}

const removeFromDept = (row) => {
  Modal.confirm({
    title: '移出部门确认',
    content: `确定将【${row.full_name}】移出当前部门吗？`,
    simple: false,
    onOk: async () => {
      await userApi.updateUser(row.id, { department_id: null })
      Message.success('已移出部门')
      fetchAll()
    }
  })
}

const handleDeleteUser = (row) => {
  Modal.confirm({
    title: '删除确认',
    content: `确定要删除成员【${row.full_name}】吗？`,
    okButtonProps: { status: 'danger' },
    simple: false,
    onOk: async () => {
      await userApi.deleteUser(row.id)
      Message.success('成员已删除')
      fetchAll()
    }
  })
}

// 仅同步部门（幂等：已存在跳过）
const handleSyncDepartmentsOnly = async () => {
  syncingDept.value = true
  try {
    const res = await userApi.syncDepartments()
    Message.success(res.message || '部门架构同步完成')
    fetchAll()
  } catch (e) {
    Message.error(e.response?.data?.detail || '同步部门失败')
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
    Message.error(e.response?.data?.detail || '获取 OneAuth 成员候选列表失败')
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

const selectUnsyncedAll = () => {
  selectedCandidateKeys.value = filteredCandidates.value
    .filter(candidate => !candidate.is_synced)
    .map(candidate => candidate.key)
}

const confirmImportCandidates = async () => {
  if (!selectedCandidateKeys.value.length) {
    Message.warning('请至少勾选一位要导入的员工')
    return
  }
  importingUsers.value = true
  try {
    const res = await userApi.importOneAuthUsers(selectedCandidateKeys.value)
    Message.success(res.message || `成功导入 ${selectedCandidateKeys.value.length} 位员工`)
    candidateDialogVisible.value = false
    fetchAll()
  } catch (e) {
    Message.error(e.response?.data?.detail || '导入员工失败')
  } finally {
    importingUsers.value = false
  }
}

// 一键全量同步
const handleSyncAllData = async () => {
  syncingAll.value = true
  try {
    const res = await userApi.syncOneAuth()
    Message.success(res.message || '全量架构与员工同步完成')
    fetchAll()
  } catch (e) {
    Message.error(e.response?.data?.detail || '同步失败')
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
    Message.error('获取配置失败')
  }
}

const saveSSOConfig = async (triggerSync = false) => {
  if (!ssoConfigForm.value.server_url) {
    Message.warning('请输入身份源服务地址')
    return
  }
  savingConfig.value = true
  try {
    await userApi.updateSSOConfig(ssoConfigForm.value)
    Message.success('身份源连接配置已保存')
    ssoConfigVisible.value = false
    if (triggerSync) {
      handleSyncAllData()
    }
  } finally {
    savingConfig.value = false
  }
}

const handleBatchDeleteUsers = () => {
  if (!selectedUsers.value.length) return
  const count = selectedUsers.value.length
  const userIds = selectedUsers.value.map(user => user.id)
  Modal.confirm({
    title: '批量删除成员',
    content: `确定永久删除选中的 ${count} 位成员吗？删除后无法恢复；内置管理员和当前登录账号会被自动保护。`,
    okText: '确认删除',
    cancelText: '取消',
    okButtonProps: { status: 'danger' },
    simple: false,
    onOk: async () => {
      batchDeleteLoading.value = true
      try {
        const res = await userApi.batchDeleteUsers(userIds)
        Message.success(res.message || `已删除 ${count} 位成员`)
        clearUserSelection()
        await fetchAll()
      } catch (e) {
        Message.error(e.response?.data?.detail || '批量删除失败')
        return false
      } finally {
        batchDeleteLoading.value = false
      }
    }
  })
}

const testSSOConfig = async () => {
  if (!ssoConfigForm.value.server_url) {
    Message.warning('请输入身份源服务地址')
    return
  }
  if (!ssoConfigForm.value.sync_username || !ssoConfigForm.value.sync_password) {
    Message.warning('请输入同步用户名和密码')
    return
  }
  testingConfig.value = true
  try {
    const res = await userApi.testSSOConfig(ssoConfigForm.value)
    Message.success(res.message || 'OneAuth 连接测试成功')
  } catch (e) {
    Message.error(e.response?.data?.detail || 'OneAuth 连接测试失败')
  } finally {
    testingConfig.value = false
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
  --app-page-gap: var(--app-space-4);
}

.btn-icon {
  margin-right: 5px;
}

.org-layout-grid {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: var(--app-space-4);
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
  border-radius: var(--app-radius-panel);
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
  border-radius: var(--app-radius-control);
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
  border-radius: var(--app-radius-panel);
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
  min-width: 0;
  padding: 20px;
  background: white;
  border-radius: var(--app-radius-panel);
  overflow: hidden;
}
.dept-members-card :deep(.arco-table-container) { overflow-x: auto; }
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
  background: var(--color-fill-1);
  border: 1px solid #bfdbfe;
  border-radius: var(--app-radius-panel);
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
