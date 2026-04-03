import { ref, computed } from 'vue'
import * as adminApi from './adminApi.js'

export function useAdmin() {
  // 状态
  const currentTab = ref('dashboard')
  const username = ref(localStorage.getItem('username') || '')
  const role = ref(localStorage.getItem('role') || 'user')
  const users = ref([])
  const stats = ref({
    total_users: 0,
    active_users: 0,
    disabled_users: 0,
    admin_count: 0,
    total_sessions: 0
  })
  const llmModels = ref([])
  const activeModelId = ref(null)

  // 弹窗状态
  const showRoleDialog = ref(false)
  const showResetDialog = ref(false)
  const showAddUserDialog = ref(false)
  const showEditDialog = ref(false)
  const showAddModelDialog = ref(false)
  const showEditModelDialog = ref(false)

  // 选中项
  const selectedUser = ref(null)
  const selectedModel = ref(null)

  // 表单数据
  const newRole = ref('user')
  const newPassword = ref('')
  const newUser = ref({
    username: '',
    password: '',
    email: '',
    full_name: '',
    role: 'user'
  })
  const editForm = ref({
    email: '',
    full_name: ''
  })
  const newModel = ref({
    name: '',
    model: '',
    base_url: '',
    api_key: '',
    temperature: 0.7,
    max_tokens: 2048,
    description: ''
  })
  const editModelForm = ref({
    name: '',
    model: '',
    base_url: '',
    api_key: '',
    temperature: 0.7,
    max_tokens: 2048,
    description: ''
  })

  // 消息提示
  const message = ref({
    show: false,
    text: '',
    type: 'success'
  })

  // 计算属性
  const isSuperAdmin = computed(() => role.value === 'super_admin')
  const roleDisplay = computed(() => {
    const roleMap = {
      'user': '普通用户',
      'admin': '管理员',
      'super_admin': '超级管理员'
    }
    return roleMap[role.value] || role.value
  })

  // 显示消息
  function showMessage(text, type = 'success') {
    message.value = { show: true, text, type }
    setTimeout(() => {
      message.value.show = false
    }, 3000)
  }

  // 处理未授权
  async function handleUnauthorized(response, onLogout) {
    if (response.status === 401) {
      let errorDetail = '登录已过期，请重新登录'
      try {
        const errorData = await response.json()
        if (errorData.detail && errorData.detail.includes('其他地方登录')) {
          errorDetail = '账号已在其他地方登录'
        }
      } catch (e) {}
      showMessage(errorDetail, 'error')
      setTimeout(() => onLogout?.(), 1500)
      return true
    }
    if (response.status === 403) {
      let errorDetail = '没有权限执行此操作'
      try {
        const errorData = await response.json()
        if (errorData.detail) {
          if (errorData.detail.includes('禁用')) {
            errorDetail = '用户已被禁用，请联系管理员'
            showMessage(errorDetail, 'error')
            setTimeout(() => onLogout?.(), 1500)
            return true
          } else {
            errorDetail = errorData.detail
          }
        }
      } catch (e) {}
      showMessage(errorDetail, 'error')
      return true
    }
    return false
  }

  // 角色文本
  function roleText(role) {
    const map = {
      'user': '普通用户',
      'admin': '管理员',
      'super_admin': '超级管理员'
    }
    return map[role] || role
  }

  // 是否是管理员
  function isAdminUser(userRole) {
    return ['admin', 'super_admin'].includes(userRole)
  }

  // 权限检查
  function canEditUser(user) {
    if (user.username === username.value) return false
    if (isSuperAdmin.value) return true
    return !isAdminUser(user.role)
  }

  function canToggleUser(user) {
    if (user.username === username.value) return false
    if (role.value === 'admin' && isAdminUser(user.role)) return false
    return true
  }

  function canResetPassword(user) {
    if (user.username === username.value) return false
    if (role.value === 'admin' && isAdminUser(user.role)) return false
    return true
  }

  function canDeleteUser(user) {
    if (!isSuperAdmin.value) return false
    if (user.username === username.value) return false
    return !isAdminUser(user.role)
  }

  // 加载数据
  async function loadDashboard(onLogout) {
    try {
      const data = await adminApi.getSystemStatus()
      stats.value = data
    } catch (error) {
      if (error.response && await handleUnauthorized(error.response, onLogout)) return
      console.error('加载仪表盘失败:', error)
    }
  }

  async function loadUsers(onLogout) {
    try {
      const data = await adminApi.getUsers()
      users.value = data.users
      stats.value.total_users = data.total
      stats.value.active_users = data.active
      stats.value.disabled_users = data.disabled
      stats.value.admin_count = data.admins
    } catch (error) {
      if (error.response && await handleUnauthorized(error.response, onLogout)) return
      console.error('加载用户列表失败:', error)
    }
  }

  async function loadLLMModels(onLogout) {
    try {
      const data = await adminApi.getLLMModels()
      llmModels.value = data.models
      activeModelId.value = data.active_model_id
    } catch (error) {
      if (error.response && await handleUnauthorized(error.response, onLogout)) return
      console.error('加载模型配置失败:', error)
    }
  }

  // 弹窗操作
  function showRoleModal(user) {
    selectedUser.value = user
    newRole.value = user.role
    showRoleDialog.value = true
  }

  function showAddUserModal() {
    newUser.value = {
      username: '',
      password: '',
      email: '',
      full_name: '',
      role: 'user'
    }
    showAddUserDialog.value = true
  }

  function showEditModal(user) {
    selectedUser.value = user
    editForm.value = {
      email: user.email || '',
      full_name: user.full_name || ''
    }
    showEditDialog.value = true
  }

  function showAddModelModal() {
    newModel.value = {
      name: '',
      model: '',
      base_url: '',
      api_key: '',
      temperature: 0.7,
      max_tokens: 2048,
      description: ''
    }
    showAddModelDialog.value = true
  }

  function showEditModelModal(model) {
    selectedModel.value = model
    editModelForm.value = {
      name: model.name,
      model: model.model,
      base_url: model.base_url,
      api_key: '',
      temperature: model.temperature,
      max_tokens: model.max_tokens,
      description: model.description || ''
    }
    showEditModelDialog.value = true
  }

  function showResetModal(user) {
    selectedUser.value = user
    newPassword.value = ''
    showResetDialog.value = true
  }

  // API操作
  async function updateRole(onLogout) {
    try {
      await adminApi.updateUserRole(selectedUser.value.username, newRole.value)
      showMessage('角色修改成功')
      showRoleDialog.value = false
      await loadUsers(onLogout)
    } catch (error) {
      showMessage(error.message || '修改失败', 'error')
    }
  }

  async function toggleUser(user, onLogout) {
    const action = user.disabled ? '启用' : '禁用'
    if (!confirm(`确定要${action}用户 "${user.username}" 吗？`)) return

    try {
      await adminApi.toggleUser(user.username)
      showMessage(`${action}成功`)
      await loadUsers(onLogout)
    } catch (error) {
      showMessage(error.message || '操作失败', 'error')
    }
  }

  async function resetPassword(onLogout) {
    if (!newPassword.value || newPassword.value.length < 6) {
      showMessage('密码长度至少6位', 'error')
      return
    }

    try {
      await adminApi.resetPassword(selectedUser.value.username, newPassword.value)
      showMessage('密码重置成功')
      showResetDialog.value = false
    } catch (error) {
      showMessage(error.message || '重置失败', 'error')
    }
  }

  async function deleteUser(user, onLogout) {
    if (!confirm(`确定要删除用户 "${user.username}" 吗？此操作不可恢复！`)) return

    try {
      await adminApi.deleteUser(user.username)
      showMessage('删除成功')
      await loadUsers(onLogout)
    } catch (error) {
      showMessage(error.message || '删除失败', 'error')
    }
  }

  async function addUser(onLogout) {
    if (!newUser.value.username || newUser.value.username.length < 3) {
      showMessage('用户名至少3个字符', 'error')
      return
    }
    if (!newUser.value.password || newUser.value.password.length < 6) {
      showMessage('密码至少6个字符', 'error')
      return
    }

    try {
      await adminApi.createUser(newUser.value)
      showMessage('用户创建成功')
      showAddUserDialog.value = false
      await loadUsers(onLogout)
    } catch (error) {
      showMessage(error.message || '创建失败', 'error')
    }
  }

  async function updateUser(onLogout) {
    try {
      await adminApi.updateUser(selectedUser.value.username, editForm.value)
      showMessage('用户信息更新成功')
      showEditDialog.value = false
      await loadUsers(onLogout)
    } catch (error) {
      showMessage(error.message || '更新失败', 'error')
    }
  }

  async function addModel(onLogout) {
    if (!newModel.value.name || !newModel.value.model || !newModel.value.base_url || !newModel.value.api_key) {
      showMessage('请填写所有必填项', 'error')
      return
    }

    try {
      await adminApi.createLLMModel(newModel.value)
      showMessage('模型配置创建成功')
      showAddModelDialog.value = false
      await loadLLMModels(onLogout)
    } catch (error) {
      showMessage(error.message || '创建失败', 'error')
    }
  }

  async function updateModel(onLogout) {
    const updateData = { ...editModelForm.value }
    if (!updateData.api_key) {
      delete updateData.api_key
    }

    try {
      await adminApi.updateLLMModel(selectedModel.value.id, updateData)
      showMessage('模型配置更新成功')
      showEditModelDialog.value = false
      await loadLLMModels(onLogout)
    } catch (error) {
      showMessage(error.message || '更新失败', 'error')
    }
  }

  async function activateModel(model, onLogout) {
    try {
      await adminApi.activateLLMModel(model.id)
      showMessage(`模型 "${model.name}" 已启用`)
      await loadLLMModels(onLogout)
    } catch (error) {
      showMessage(error.message || '启用失败', 'error')
    }
  }

  async function deleteModel(model, onLogout) {
    if (!confirm(`确定要删除模型配置 "${model.name}" 吗？此操作不可恢复！`)) return

    try {
      await adminApi.deleteLLMModel(model.id)
      showMessage('删除成功')
      await loadLLMModels(onLogout)
    } catch (error) {
      showMessage(error.message || '删除失败', 'error')
    }
  }

  return {
    // 状态
    currentTab,
    username,
    role,
    users,
    stats,
    llmModels,
    activeModelId,
    showRoleDialog,
    showResetDialog,
    showAddUserDialog,
    showEditDialog,
    showAddModelDialog,
    showEditModelDialog,
    selectedUser,
    selectedModel,
    newRole,
    newPassword,
    newUser,
    editForm,
    newModel,
    editModelForm,
    message,
    // 计算属性
    isSuperAdmin,
    roleDisplay,
    // 方法
    showMessage,
    handleUnauthorized,
    roleText,
    isAdminUser,
    canEditUser,
    canToggleUser,
    canResetPassword,
    canDeleteUser,
    loadDashboard,
    loadUsers,
    loadLLMModels,
    showRoleModal,
    showAddUserModal,
    showEditModal,
    showAddModelModal,
    showEditModelModal,
    showResetModal,
    updateRole,
    toggleUser,
    resetPassword,
    deleteUser,
    addUser,
    updateUser,
    addModel,
    updateModel,
    activateModel,
    deleteModel
  }
}
