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
        <div 
          class="menu-item" 
          :class="{ active: currentTab === 'tools' }"
          @click="currentTab = 'tools'"
        >
          🛠️ 工具管理
        </div>
        <div 
          class="menu-item" 
          :class="{ active: currentTab === 'skills' }"
          @click="currentTab = 'skills'"
        >
          ⚡ 技能管理
        </div>
        <div 
          class="menu-item" 
          :class="{ active: currentTab === 'sessions' }"
          @click="currentTab = 'sessions'"
        >
          💬 会话管理
        </div>
        <div 
          class="menu-item" 
          :class="{ active: currentTab === 'system' }"
          @click="currentTab = 'system'"
        >
          ⚡ 系统设置
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

        <!-- 工具管理 -->
        <div v-if="currentTab === 'tools'" class="tab-content">
          <div class="section-header">
            <h2>工具管理</h2>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>工具名称</th>
                  <th>描述</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="tool in tools" :key="tool.name">
                  <td>{{ tool.name }}</td>
                  <td>{{ tool.description }}</td>
                  <td>
                    <span class="status-badge active">可用</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="tools.length === 0" class="empty-state">
              暂无可用工具
            </div>
          </div>
          <div class="config-form" style="margin-top: 20px;">
            <h3>工具配置说明</h3>
            <div class="info-box">
              <p><strong>web_search</strong> - 网络搜索工具，用于获取最新信息</p>
              <p><strong>calculator</strong> - 计算器工具，用于数学计算</p>
              <p><strong>file_write</strong> - 文件写入工具，用于保存内容到文件</p>
              <p><strong>skill_execute</strong> - Skill执行工具，用于执行自定义技能</p>
            </div>
          </div>
        </div>

        <!-- 技能管理 -->
        <div v-if="currentTab === 'skills'" class="tab-content">
          <div class="section-header">
            <h2>技能管理</h2>
            <button class="btn-add" @click="showAddSkillModal">
              + 添加技能
            </button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>技能名称</th>
                  <th>描述</th>
                  <th>分类</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="skill in skills" :key="skill.name">
                  <td>{{ skill.name }}</td>
                  <td>{{ skill.description }}</td>
                  <td>
                    <span class="role-badge" :class="skill.category">
                      {{ skill.category === 'general' ? '通用' : skill.category === 'productivity' ? '生产力' : skill.category }}
                    </span>
                  </td>
                  <td>
                    <span :class="['status-badge', skill.enabled ? 'active' : 'disabled']">
                      {{ skill.enabled ? '启用' : '禁用' }}
                    </span>
                  </td>
                  <td>
                    <div class="action-buttons">
                      <button 
                        class="btn-small btn-edit"
                        @click="showEditSkillModal(skill)"
                      >
                        编辑
                      </button>
                      <button 
                        class="btn-small btn-test"
                        @click="showTestSkillModal(skill)"
                      >
                        测试
                      </button>
                      <button 
                        class="btn-small"
                        :class="skill.enabled ? 'btn-disable' : 'btn-enable'"
                        @click="toggleSkill(skill, handleLogout)"
                      >
                        {{ skill.enabled ? '禁用' : '启用' }}
                      </button>
                      <button 
                        class="btn-small btn-delete"
                        @click="deleteSkill(skill, handleLogout)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="skills.length === 0" class="empty-state">
              暂无技能，请点击"添加技能"按钮创建
            </div>
          </div>
          <div class="config-form" style="margin-top: 20px;">
            <h3>技能配置说明</h3>
            <div class="info-box">
              <p><strong>技能文件格式</strong> - 技能使用 Markdown 格式定义，保存在 skills/skills_dir 目录下</p>
              <p><strong>参数定义</strong> - 技能可以定义多个参数，支持 string、int、float、bool 类型</p>
              <p><strong>脚本支持</strong> - 技能可以包含 Python 脚本，通过 parameters 变量访问参数</p>
              <p><strong>提示词模板</strong> - 支持系统提示词和用户提示词模板</p>
            </div>
          </div>
        </div>

        <!-- 会话管理 -->
        <div v-if="currentTab === 'sessions'" class="tab-content">
          <div class="section-header">
            <h2>会话管理</h2>
            <button class="btn-add" @click="loadSessions(handleLogout)">
              🔄 刷新
            </button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>会话ID</th>
                  <th>用户ID</th>
                  <th>标题</th>
                  <th>消息数</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="session in sessions" :key="session.session_id">
                  <td>{{ session.session_id.substring(0, 8) }}...</td>
                  <td>{{ session.user_id || '匿名' }}</td>
                  <td>{{ session.title }}</td>
                  <td>{{ session.message_count || 0 }}</td>
                  <td>{{ formatTime(session.created_at) }}</td>
                  <td>
                    <div class="action-buttons">
                      <button 
                        class="btn-small btn-delete"
                        @click="deleteSession(session.session_id, handleLogout)"
                      >
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="sessions.length === 0" class="empty-state">
              暂无会话记录
            </div>
          </div>
        </div>

        <!-- 系统设置 -->
        <div v-if="currentTab === 'system'" class="tab-content">
          <h2>系统设置</h2>
          <div class="config-form">
            <div class="form-group">
              <label>站点名称</label>
              <input v-model="systemConfig.site_name" type="text" placeholder="输入站点名称" />
            </div>
            <div class="form-group">
              <label>默认上下文长度</label>
              <input v-model.number="systemConfig.max_context_length" type="number" min="1" max="50" />
            </div>
            <div class="form-group">
              <label>默认温度 (0-2)</label>
              <input v-model.number="systemConfig.default_temperature" type="number" min="0" max="2" step="0.1" />
            </div>
            <div class="form-group">
              <label>最大Token数</label>
              <input v-model.number="systemConfig.max_tokens" type="number" min="1" max="8192" />
            </div>
            <div class="form-group">
              <label>会话过期天数</label>
              <input v-model.number="systemConfig.session_expire_days" type="number" min="1" max="30" />
            </div>
            <div class="form-group">
              <label class="checkbox-label">
                <input v-model="systemConfig.enable_streaming" type="checkbox" />
                启用流式响应
              </label>
            </div>
            <button class="btn-save" @click="saveSystemConfig(handleLogout)">
              保存配置
            </button>
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

    <!-- 添加技能弹窗 -->
    <div v-if="showAddSkillDialog" class="modal-overlay" @click.self="showAddSkillDialog = false">
      <div class="modal" style="max-width: 600px; max-height: 90vh; overflow-y: auto;">
        <h3>添加技能</h3>
        <div class="form-group">
          <label>技能名称 *</label>
          <input v-model="newSkill.name" type="text" placeholder="输入技能名称" />
        </div>
        <div class="form-group">
          <label>描述 *</label>
          <textarea v-model="newSkill.description" rows="3" placeholder="输入技能描述"></textarea>
        </div>
        <div class="form-group">
          <label>分类</label>
          <select v-model="newSkill.category">
            <option value="general">通用</option>
            <option value="productivity">生产力</option>
            <option value="entertainment">娱乐</option>
            <option value="education">教育</option>
            <option value="finance">金融</option>
            <option value="custom">自定义</option>
          </select>
        </div>
        <div class="form-group">
          <label>参数列表</label>
          <div v-for="(param, index) in newSkill.parameters" :key="index" class="param-group">
            <div class="param-row">
              <input v-model="param.name" type="text" placeholder="参数名称" />
              <select v-model="param.type">
                <option value="string">string</option>
                <option value="int">int</option>
                <option value="float">float</option>
                <option value="bool">bool</option>
              </select>
              <input v-model="param.description" type="text" placeholder="描述" />
              <label class="checkbox-label">
                <input v-model="param.required" type="checkbox" /> 必填
              </label>
              <button v-if="newSkill.parameters.length > 1" class="btn-remove-param" @click="removeSkillParam(newSkill, index)">×</button>
            </div>
          </div>
          <button class="btn-add-param" @click="addSkillParam(newSkill)">+ 添加参数</button>
        </div>
        <div class="form-group">
          <label>系统提示词</label>
          <textarea v-model="newSkill.system_prompt" rows="3" placeholder="系统提示词（可选）"></textarea>
        </div>
        <div class="form-group">
          <label>用户提示词模板</label>
          <textarea v-model="newSkill.user_prompt" rows="3" placeholder="用户提示词模板，使用 {{参数名}} 引用参数（可选）"></textarea>
        </div>
        <div class="form-group">
          <label>Python 脚本</label>
          <textarea v-model="newSkill.script" rows="5" placeholder="Python脚本，使用 parameters['参数名'] 访问参数（可选）"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showAddSkillDialog = false">取消</button>
          <button class="btn-confirm" @click="addSkill(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 编辑技能弹窗 -->
    <div v-if="showEditSkillDialog" class="modal-overlay" @click.self="showEditSkillDialog = false">
      <div class="modal" style="max-width: 600px; max-height: 90vh; overflow-y: auto;">
        <h3>编辑技能</h3>
        <p>技能: {{ selectedSkill?.name }}</p>
        <div class="form-group">
          <label>技能名称</label>
          <input v-model="editSkillForm.name" type="text" placeholder="输入技能名称" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="editSkillForm.description" rows="3" placeholder="输入技能描述"></textarea>
        </div>
        <div class="form-group">
          <label>分类</label>
          <select v-model="editSkillForm.category">
            <option value="general">通用</option>
            <option value="productivity">生产力</option>
            <option value="entertainment">娱乐</option>
            <option value="education">教育</option>
            <option value="finance">金融</option>
            <option value="custom">自定义</option>
          </select>
        </div>
        <div class="form-group">
          <label>参数列表</label>
          <div v-for="(param, index) in editSkillForm.parameters" :key="index" class="param-group">
            <div class="param-row">
              <input v-model="param.name" type="text" placeholder="参数名称" />
              <select v-model="param.type">
                <option value="string">string</option>
                <option value="int">int</option>
                <option value="float">float</option>
                <option value="bool">bool</option>
              </select>
              <input v-model="param.description" type="text" placeholder="描述" />
              <label class="checkbox-label">
                <input v-model="param.required" type="checkbox" /> 必填
              </label>
              <button v-if="editSkillForm.parameters.length > 1" class="btn-remove-param" @click="removeSkillParam(editSkillForm, index)">×</button>
            </div>
          </div>
          <button class="btn-add-param" @click="addSkillParam(editSkillForm)">+ 添加参数</button>
        </div>
        <div class="form-group">
          <label>系统提示词</label>
          <textarea v-model="editSkillForm.system_prompt" rows="3" placeholder="系统提示词（可选）"></textarea>
        </div>
        <div class="form-group">
          <label>用户提示词模板</label>
          <textarea v-model="editSkillForm.user_prompt" rows="3" placeholder="用户提示词模板，使用 {{参数名}} 引用参数（可选）"></textarea>
        </div>
        <div class="form-group">
          <label>Python 脚本</label>
          <textarea v-model="editSkillForm.script" rows="5" placeholder="Python脚本，使用 parameters['参数名'] 访问参数（可选）"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showEditSkillDialog = false">取消</button>
          <button class="btn-confirm" @click="updateSkill(handleLogout)">确认</button>
        </div>
      </div>
    </div>

    <!-- 测试技能弹窗 -->
    <div v-if="showTestSkillDialog" class="modal-overlay" @click.self="showTestSkillDialog = false">
      <div class="modal" style="max-width: 500px;">
        <h3>测试技能: {{ selectedSkill?.name }}</h3>
        <div class="form-group">
          <label>测试参数</label>
          <div v-for="param in selectedSkill?.parameters" :key="param.name" class="param-group">
            <input 
              v-model="testSkillParams[param.name]" 
              type="text" 
              :placeholder="param.description || param.name"
              :required="param.required"
            />
          </div>
          <div v-if="!selectedSkill?.parameters || selectedSkill.parameters.length === 0" class="empty-state">
            该技能没有参数
          </div>
        </div>
        <button class="btn-save" @click="testSkill(handleLogout)" style="margin-bottom: 15px;">执行测试</button>
        <div v-if="testSkillResult" class="test-result">
          <h4>测试结果</h4>
          <div :class="['result-box', testSkillResult.success ? 'success' : 'error']">
            <p class="result-status">{{ testSkillResult.success ? '✓ 成功' : '✗ 失败' }}</p>
            <pre v-if="testSkillResult.output">{{ testSkillResult.output }}</pre>
            <p v-if="testSkillResult.error" class="result-error">{{ testSkillResult.error }}</p>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-cancel" @click="showTestSkillDialog = false">关闭</button>
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
    this.loadTools(this.handleLogout)
    this.loadSkills(this.handleLogout)
    this.loadSessions(this.handleLogout)
    this.loadSystemConfig(this.handleLogout)
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
    },
    formatTime(timestamp) {
      if (!timestamp) return '-'
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
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

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
  color: #555;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.info-box {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-top: 10px;
}

.info-box p {
  margin: 8px 0;
  font-size: 14px;
  color: #555;
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

.form-group textarea {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: monospace;
  resize: vertical;
  min-height: 60px;
}

.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.btn-test {
  background-color: #2196f3;
  color: white;
}

.btn-test:hover {
  background-color: #1976d2;
}

.param-group {
  margin-bottom: 10px;
}

.param-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.param-row input,
.param-row select {
  flex: 1;
  min-width: 100px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.param-row .checkbox-label {
  margin-left: 0;
}

.btn-add-param {
  margin-top: 10px;
  padding: 8px 16px;
  background-color: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.btn-add-param:hover {
  background-color: #5a6fd6;
}

.btn-remove-param {
  padding: 6px 10px;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
}

.btn-remove-param:hover {
  background-color: #d32f2f;
}

.test-result {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.test-result h4 {
  margin-bottom: 10px;
  color: #333;
}

.result-box {
  padding: 15px;
  border-radius: 8px;
}

.result-box.success {
  background-color: #e8f5e9;
  border: 1px solid #c8e6c9;
}

.result-box.error {
  background-color: #ffebee;
  border: 1px solid #ffcdd2;
}

.result-status {
  font-weight: 600;
  margin-bottom: 10px;
}

.result-box.success .result-status {
  color: #388e3c;
}

.result-box.error .result-status {
  color: #d32f2f;
}

.result-box pre {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.result-error {
  color: #d32f2f;
  font-size: 14px;
}
</style>
