<template>
  <div class="admin-container">
    <!-- 顶部导航 -->
    <div class="admin-header">
      <h1>管理员控制台</h1>
      <div class="header-actions">
        <span class="user-info">{{ username }} ({{ roleDisplay }})</span>
        <button class="btn-back" @click="goBack">返回聊天</button>
        <button class="btn-logout" @click="handleLogout">退出登录</button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="admin-content">
      <!-- 侧边栏 -->
      <div class="admin-sidebar">
        <div 
          class="menu-item" 
          :class="{ active: currentTab === 'dashboard' }"
          @click="currentTab = 'dashboard'"
        >
          📊 仪表盘
        </div>
        <div 
          class="menu-item" 
          :class="{ active: currentTab === 'users' }"
          @click="currentTab = 'users'"
        >
          👥 用户管理
        </div>
        <div 
          class="menu-item" 
          :class="{ active: currentTab === 'config' }"
          @click="currentTab = 'config'"
        >
          ⚙️ 模型配置
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="admin-main">
        <!-- 仪表盘 -->
        <div v-if="currentTab === 'dashboard'" class="tab-content">
          <h2>系统概览</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_users }}</div>
              <div class="stat-label">总用户数</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.active_users }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.disabled_users }}</div>
              <div class="stat-label">禁用用户</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.admin_count }}</div>
              <div class="stat-label">管理员</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ stats.total_sessions }}</div>
              <div class="stat-label">总会话数</div>
            </div>
          </div>
        </div>

        <!-- 用户管理 -->
        <div v-if="currentTab === 'users'" class="tab-content">
          <div class="section-header">
            <h2>用户管理</h2>
            <button class="btn-add" @click="showAddUserModal">
              + 添加用户
            </button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in users" :key="user.username">
                  <td>{{ user.username }}</td>
                  <td>{{ user.email || '-' }}</td>
                  <td>
                    <span :class="['role-badge', user.role]">
                      {{ roleText(user.role) }}
                    </span>
                  </td>
                  <td>
                    <span :class="['status-badge', user.disabled ? 'disabled' : 'active']">
                      {{ user.disabled ? '禁用' : '正常' }}
                    </span>
                  </td>
                  <td>
                    <div class="action-buttons">
                      <button 
                        v-if="canEditUser(user)"
                        class="btn-small btn-edit"
                        @click="showEditModal(user)"
                      >
                        编辑
                      </button>
                      <button 
                        v-if="isSuperAdmin && user.username !== username"
                        class="btn-small btn-role"
                        @click="showRoleModal(user)"
                      >
                        角色
                      </button>
                      <button 
                        v-if="canToggleUser(user)"
                        class="btn-small"
                        :class="user.disabled ? 'btn-enable' : 'btn-disable'"
                        @click="toggleUser(user, handleLogout)"
                      >
                        {{ user.disabled ? '启用' : '禁用' }}
                      </button>
                      <button 
                        v-if="canResetPassword(user)"
                        class="btn-small btn-reset"
                        @click="showResetModal(user)"
                      >
                        密码
                      </button>
                      <button 
                        v-if="canDeleteUser(user)"
                        class="btn-small btn-delete"
                        @click="deleteUser(user, handleLogout)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 模型配置 -->
        <div v-if="currentTab === 'config'" class="tab-content">
          <div class="section-header">
            <h2>模型配置管理</h2>
            <button class="btn-add" @click="showAddModelModal">
              + 添加模型
            </button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>状态</th>
                  <th>名称</th>
                  <th>模型</th>
                  <th>Base URL</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="model in llmModels" :key="model.id">
                  <td>
                    <span :class="['status-badge', model.is_active ? 'active' : 'disabled']">
                      {{ model.is_active ? '启用中' : '未启用' }}
                    </span>
                  </td>
                  <td>{{ model.name }}</td>
                  <td>{{ model.model }}</td>
                  <td>{{ model.base_url }}</td>
                  <td>
                    <div class="action-buttons">
                      <button 
                        v-if="!model.is_active"
                        class="btn-small btn-enable"
                        @click="activateModel(model, handleLogout)"
                      >
                        启用
                      </button>
                      <button 
                        class="btn-small btn-edit"
                        @click="showEditModelModal(model)"
                      >
                        编辑
                      </button>
                      <button 
                        class="btn-small btn-delete"
                        @click="deleteModel(model, handleLogout)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="llmModels.length === 0" class="empty-state">
              暂无模型配置，请点击"添加模型"按钮创建
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 角色修改弹窗 -->
    <div v-if="showRoleDialog" class="modal-overlay" @click.self="showRoleDialog = false">
      <div class="modal">
        <h3>修改用户角色</h3>
        <p>用户: {{ selectedUser?.username }}</p>
        <div class="form-group">
          <label>选择角色</label>
          <select v-model="newRole">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
            <option value="super_admin">超级管理员</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showRoleDialog = false">取消</button>
          <button class="btn-confirm" @click="updateRole(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 重置密码弹窗 -->
    <div v-if="showResetDialog" class="modal-overlay" @click.self="showResetDialog = false">
      <div class="modal">
        <h3>重置密码</h3>
        <p>用户: {{ selectedUser?.username }}</p>
        <div class="form-group">
          <label>新密码</label>
          <input v-model="newPassword" type="password" placeholder="输入新密码" />
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showResetDialog = false">取消</button>
          <button class="btn-confirm" @click="resetPassword(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 添加用户弹窗 -->
    <div v-if="showAddUserDialog" class="modal-overlay" @click.self="showAddUserDialog = false">
      <div class="modal">
        <h3>添加新用户</h3>
        <div class="form-group">
          <label>用户名 *</label>
          <input v-model="newUser.username" type="text" placeholder="输入用户名" />
        </div>
        <div class="form-group">
          <label>密码 *</label>
          <input v-model="newUser.password" type="password" placeholder="输入密码" />
        </div>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="newUser.email" type="email" placeholder="输入邮箱" />
        </div>
        <div class="form-group">
          <label>全名</label>
          <input v-model="newUser.full_name" type="text" placeholder="输入全名" />
        </div>
        <div class="form-group" v-if="isSuperAdmin">
          <label>角色</label>
          <select v-model="newUser.role">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
            <option value="super_admin">超级管理员</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showAddUserDialog = false">取消</button>
          <button class="btn-confirm" @click="addUser(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 编辑用户弹窗 -->
    <div v-if="showEditDialog" class="modal-overlay" @click.self="showEditDialog = false">
      <div class="modal">
        <h3>编辑用户</h3>
        <p>用户: {{ selectedUser?.username }}</p>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="editForm.email" type="email" placeholder="输入邮箱" />
        </div>
        <div class="form-group">
          <label>全名</label>
          <input v-model="editForm.full_name" type="text" placeholder="输入全名" />
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showEditDialog = false">取消</button>
          <button class="btn-confirm" @click="updateUser(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 添加模型弹窗 -->
    <div v-if="showAddModelDialog" class="modal-overlay" @click.self="showAddModelDialog = false">
      <div class="modal">
        <h3>添加模型配置</h3>
        <div class="form-group">
          <label>名称 *</label>
          <input v-model="newModel.name" type="text" placeholder="例如：OpenAI GPT-4" />
        </div>
        <div class="form-group">
          <label>模型名称 *</label>
          <input v-model="newModel.model" type="text" placeholder="例如：gpt-4" />
        </div>
        <div class="form-group">
          <label>Base URL *</label>
          <input v-model="newModel.base_url" type="text" placeholder="https://api.openai.com/v1" />
        </div>
        <div class="form-group">
          <label>API Key *</label>
          <input v-model="newModel.api_key" type="password" placeholder="输入API Key" />
        </div>
        <div class="form-group">
          <label>Temperature (0-2)</label>
          <input v-model.number="newModel.temperature" type="number" min="0" max="2" step="0.1" />
        </div>
        <div class="form-group">
          <label>Max Tokens</label>
          <input v-model.number="newModel.max_tokens" type="number" min="1" max="8192" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <input v-model="newModel.description" type="text" placeholder="模型描述（可选）" />
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showAddModelDialog = false">取消</button>
          <button class="btn-confirm" @click="addModel(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 编辑模型弹窗 -->
    <div v-if="showEditModelDialog" class="modal-overlay" @click.self="showEditModelDialog = false">
      <div class="modal">
        <h3>编辑模型配置</h3>
        <p>模型: {{ selectedModel?.name }}</p>
        <div class="form-group">
          <label>名称</label>
          <input v-model="editModelForm.name" type="text" placeholder="例如：OpenAI GPT-4" />
        </div>
        <div class="form-group">
          <label>模型名称</label>
          <input v-model="editModelForm.model" type="text" placeholder="例如：gpt-4" />
        </div>
        <div class="form-group">
          <label>Base URL</label>
          <input v-model="editModelForm.base_url" type="text" placeholder="https://api.openai.com/v1" />
        </div>
        <div class="form-group">
          <label>API Key (留空则不修改)</label>
          <input v-model="editModelForm.api_key" type="password" placeholder="输入新的API Key" />
        </div>
        <div class="form-group">
          <label>Temperature (0-2)</label>
          <input v-model.number="editModelForm.temperature" type="number" min="0" max="2" step="0.1" />
        </div>
        <div class="form-group">
          <label>Max Tokens</label>
          <input v-model.number="editModelForm.max_tokens" type="number" min="1" max="8192" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <input v-model="editModelForm.description" type="text" placeholder="模型描述（可选）" />
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showEditModelDialog = false">取消</button>
          <button class="btn-confirm" @click="updateModel(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 提示消息 -->
    <div v-if="message.show" :class="['toast', message.type]">
      {{ message.text }}
    </div>
  </div>
</template>

<script>
import { useAdmin } from './useAdmin.js'

export default {
  name: 'Admin',
  setup() {
    const admin = useAdmin()
    return {
      ...admin
    }
  },
  mounted() {
    this.checkAdmin()
    this.loadDashboard(this.handleLogout)
    this.loadUsers(this.handleLogout)
    this.loadLLMModels(this.handleLogout)
  },
  methods: {
    checkAdmin() {
      if (!['admin', 'super_admin'].includes(this.role)) {
        this.showMessage('没有管理员权限', 'error')
        setTimeout(() => {
          this.$emit('back')
        }, 1500)
      }
    },
    goBack() {
      this.$emit('back')
    },
    handleLogout() {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      this.$emit('logout')
    }
  }
}
</script>

<style scoped>
.admin-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.admin-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.admin-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-info {
  font-size: 14px;
  opacity: 0.9;
}

.btn-back, .btn-logout {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
}

.btn-back {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-back:hover {
  background-color: rgba(255, 255, 255, 0.3);
}

.btn-logout {
  background-color: #f44336;
  color: white;
}

.btn-logout:hover {
  background-color: #d32f2f;
}

.admin-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.admin-sidebar {
  width: 200px;
  background-color: white;
  border-right: 1px solid #e0e0e0;
  padding: 20px 0;
}

.menu-item {
  padding: 15px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: #555;
}

.menu-item:hover {
  background-color: #f5f5f5;
  color: #667eea;
}

.menu-item.active {
  background-color: #e8eaff;
  color: #667eea;
  border-left: 3px solid #667eea;
}

.admin-main {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.tab-content h2 {
  margin-bottom: 20px;
  color: #333;
  font-size: 18px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
}

.stat-card {
  background-color: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.table-container {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #555;
  font-size: 14px;
}

.data-table td {
  font-size: 14px;
  color: #333;
}

.role-badge, .status-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.user {
  background-color: #e3f2fd;
  color: #1976d2;
}

.role-badge.admin {
  background-color: #fff3e0;
  color: #f57c00;
}

.role-badge.super_admin {
  background-color: #fce4ec;
  color: #c2185b;
}

.status-badge.active {
  background-color: #e8f5e9;
  color: #388e3c;
}

.status-badge.disabled {
  background-color: #ffebee;
  color: #d32f2f;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-role {
  background-color: #667eea;
  color: white;
}

.btn-role:hover {
  background-color: #5a6fd6;
}

.btn-disable {
  background-color: #ff9800;
  color: white;
}

.btn-disable:hover {
  background-color: #f57c00;
}

.btn-enable {
  background-color: #4caf50;
  color: white;
}

.btn-enable:hover {
  background-color: #45a049;
}

.btn-reset {
  background-color: #2196f3;
  color: white;
}

.btn-reset:hover {
  background-color: #1976d2;
}

.btn-delete {
  background-color: #f44336;
  color: white;
}

.btn-delete:hover {
  background-color: #d32f2f;
}

.btn-edit {
  background-color: #9c27b0;
  color: white;
}

.btn-edit:hover {
  background-color: #7b1fa2;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn-add {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-add:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.config-form {
  background-color: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  max-width: 500px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
}

.btn-save {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-save:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background-color: white;
  padding: 30px;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal h3 {
  margin-bottom: 15px;
  color: #333;
}

.modal p {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-cancel, .btn-confirm {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.btn-cancel {
  background-color: #f5f5f5;
  color: #666;
}

.btn-cancel:hover {
  background-color: #e0e0e0;
}

.btn-confirm {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-confirm:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  z-index: 1001;
  animation: slideDown 0.3s ease;
}

.toast.success {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
}

.toast.error {
  background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>
