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
  background-color: #0f172a;
}

.admin-header {
  background: #0f172a;
  color: #f1f5f9;
  padding: 16px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #1e293b;
}

.admin-header h1 {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: -0.2px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  font-size: 13px;
  color: #94a3b8;
}

.btn-back, .btn-logout {
  padding: 7px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-back {
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.14);
  color: #f1f5f9;
}

.btn-logout {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.btn-logout:hover {
  background: rgba(239, 68, 68, 0.25);
}

.admin-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.admin-sidebar {
  width: 220px;
  background-color: #1e293b;
  border-right: 1px solid #334155;
  padding: 16px 0;
  flex-shrink: 0;
}

.menu-item {
  padding: 12px 24px;
  margin: 2px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 14px;
  color: #94a3b8;
  font-weight: 500;
}

.menu-item:hover {
  background-color: #334155;
  color: #e2e8f0;
}

.menu-item.active {
  background-color: rgba(217, 119, 6, 0.12);
  color: #d97706;
  box-shadow: none;
}

.admin-main {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
}

.tab-content h2 {
  margin-bottom: 24px;
  color: #f1f5f9;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.3px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.stat-card {
  background: #1e293b;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #334155;
  text-align: center;
  transition: box-shadow 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #d97706;
  margin-bottom: 6px;
  font-variant-numeric: tabular-nums;
  letter-spacing: -1px;
}

.stat-label {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}

.table-container {
  background: #1e293b;
  border-radius: 12px;
  border: 1px solid #334155;
  overflow: hidden;
}

.empty-state {
  padding: 48px;
  text-align: center;
  color: #64748b;
  font-size: 14px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #334155;
}

.data-table th {
  background-color: #1e293b;
  font-weight: 600;
  color: #94a3b8;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table td {
  font-size: 14px;
  color: #cbd5e1;
}

.data-table tbody tr:hover {
  background-color: rgba(51, 65, 85, 0.4);
}

.role-badge, .status-badge {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  display: inline-block;
}

.role-badge.user {
  background-color: rgba(37, 99, 235, 0.15);
  color: #60a5fa;
}

.role-badge.admin {
  background-color: rgba(217, 119, 6, 0.15);
  color: #fbbf24;
}

.role-badge.super_admin {
  background-color: rgba(219, 39, 119, 0.15);
  color: #f472b6;
}

.status-badge.active {
  background-color: rgba(5, 150, 105, 0.15);
  color: #34d399;
}

.status-badge.disabled {
  background-color: rgba(220, 38, 38, 0.15);
  color: #f87171;
}

.action-buttons {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.btn-small {
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.15s ease;
  background: rgba(51, 65, 85, 0.5);
  color: #94a3b8;
}

.btn-small:hover {
  background: #475569;
  color: #e2e8f0;
}

.btn-role {
  background: rgba(217, 119, 6, 0.15);
  color: #fbbf24;
  border-color: rgba(217, 119, 6, 0.3);
}

.btn-role:hover {
  background: rgba(217, 119, 6, 0.25);
}

.btn-disable {
  background: rgba(234, 88, 12, 0.15);
  color: #fb923c;
  border-color: rgba(234, 88, 12, 0.3);
}

.btn-disable:hover {
  background: rgba(234, 88, 12, 0.25);
}

.btn-enable {
  background: rgba(5, 150, 105, 0.15);
  color: #34d399;
  border-color: rgba(5, 150, 105, 0.3);
}

.btn-enable:hover {
  background: rgba(5, 150, 105, 0.25);
}

.btn-reset {
  background: rgba(37, 99, 235, 0.15);
  color: #60a5fa;
  border-color: rgba(37, 99, 235, 0.3);
}

.btn-reset:hover {
  background: rgba(37, 99, 235, 0.25);
}

.btn-delete {
  background: rgba(220, 38, 38, 0.15);
  color: #f87171;
  border-color: rgba(220, 38, 38, 0.3);
}

.btn-delete:hover {
  background: rgba(220, 38, 38, 0.25);
}

.btn-edit {
  background: rgba(124, 58, 237, 0.15);
  color: #a78bfa;
  border-color: rgba(124, 58, 237, 0.3);
}

.btn-edit:hover {
  background: rgba(124, 58, 237, 0.25);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn-add {
  padding: 9px 20px;
  background: #d97706;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
}

.btn-add:hover {
  background: #b45309;
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.25);
}

.config-form {
  background: #1e293b;
  padding: 32px;
  border-radius: 12px;
  border: 1px solid #334155;
  max-width: 500px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #94a3b8;
  font-size: 13px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid #334155;
  border-radius: 8px;
  font-size: 14px;
  color: #cbd5e1;
  transition: all 0.2s ease;
  font-family: inherit;
  background-color: #0f172a;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(217, 119, 6, 0.15);
}

.btn-save {
  width: 100%;
  padding: 11px;
  background: #d97706;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-save:hover:not(:disabled) {
  background: #b45309;
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.25);
}

.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1e293b;
  padding: 32px;
  border-radius: 16px;
  width: 90%;
  max-width: 420px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid #334155;
}

.modal h3 {
  margin-bottom: 8px;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 600;
}

.modal p {
  color: #94a3b8;
  margin-bottom: 20px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 24px;
}

.btn-cancel, .btn-confirm {
  padding: 9px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s ease;
}

.btn-cancel {
  background: rgba(51, 65, 85, 0.5);
  color: #94a3b8;
}

.btn-cancel:hover {
  background: #475569;
  color: #e2e8f0;
}

.btn-confirm {
  background: #d97706;
  color: white;
}

.btn-confirm:hover {
  background: #b45309;
}

.toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 10px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  z-index: 1001;
  animation: slideDown 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.toast.success {
  background: #059669;
}

.toast.error {
  background: #dc2626;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-16px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}
</style>
