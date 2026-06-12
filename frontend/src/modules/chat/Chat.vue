<template>
  <div class="chat-container">
    <!-- 侧边栏 - 会话列表 -->
    <div class="sidebar" :class="{ 'sidebar-open': showSidebar }">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createNewSession(handleLogout)">
          <span>+</span> 新会话
        </button>
      </div>
      
      <div class="session-list">
        <div 
          v-for="session in sessions" 
          :key="session.session_id"
          class="session-item"
          :class="{ active: currentSessionId === session.session_id }"
          @click="switchSession(session.session_id, handleLogout)"
        >
          <!-- 重命名输入框 -->
          <div v-if="editingSessionId === session.session_id" class="rename-input-container">
            <input 
              v-model="editingTitle"
              @keyup.enter="confirmRename(session.session_id, handleLogout)"
              @keyup.esc="cancelRename"
              @blur="confirmRename(session.session_id, handleLogout)"
              ref="renameInput"
              class="rename-input"
            />
          </div>
          <!-- 会话标题显示 -->
          <div v-else class="session-title" @dblclick.stop="startRename(session)">
            {{ session.title }}
          </div>
          <div class="session-meta">
            {{ formatDate(session.updated_at) }} · {{ session.message_count }}条消息
          </div>
          <!-- 操作按钮 -->
          <div class="session-actions">
            <button 
              class="action-btn rename-btn" 
              @click.stop="startRename(session)"
              title="重命名"
            >
              ✎
            </button>
            <button 
              class="action-btn delete-btn" 
              @click.stop="deleteSession(session.session_id, handleLogout)"
              title="删除会话"
            >
              ×
            </button>
          </div>
        </div>
      </div>
      
    </div>
    
    <!-- 主聊天区域 -->
    <div class="main-content">
      <!-- 顶部栏 -->
      <div class="chat-header">
        <button class="menu-btn" @click="toggleSidebar">
          ☰
        </button>
        <h1>{{ currentSessionTitle || 'AI 聊天助手' }}</h1>
        <!-- 个人管理下拉菜单 -->
        <div class="user-menu-container">
          <button class="user-menu-btn" @click="toggleUserMenu">
            👤
          </button>
          <div v-if="showUserMenu" class="user-menu-dropdown">
            <div class="user-info-header">
              <div class="user-avatar">👤</div>
              <div class="user-details">
                <div class="user-name">{{ username }}</div>
                <div class="user-role">{{ roleDisplay }}</div>
              </div>
            </div>
            <hr class="menu-divider" />
            <button v-if="isAdmin" class="menu-item" @click="goToAdmin">
              ⚙️ 管理后台
            </button>
            <button class="menu-item" @click="changePassword">
              🔒 修改密码
            </button>
            <button class="menu-item" @click="showAccountSettings">
              ⚙️ 账户设置
            </button>
            <hr class="menu-divider" />
            <div class="menu-theme-section">
              <button class="menu-item" @click="showThemeSubmenu = !showThemeSubmenu">
                🎨 主题
                <span class="theme-expand-icon" :class="{ open: showThemeSubmenu }">▼</span>
              </button>
              <div v-if="showThemeSubmenu" class="theme-inline-list">
                <button
                  v-for="(info, key) in THEMES"
                  :key="key"
                  class="theme-inline-item"
                  :class="{ active: activeTheme === key }"
                  @click="selectTheme(key)"
                >
                  <span class="theme-inline-icon">{{ info.icon }}</span>
                  <span>{{ info.label }}</span>
                </button>
              </div>
            </div>
            <hr class="menu-divider" />
            <button class="menu-item logout-item" @click="handleLogout">
              🚪 退出登录
            </button>
          </div>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="chat-messages" ref="messagesContainer">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <h2>👋 欢迎使用 AI 聊天助手</h2>
          <p>我可以帮你解答问题、编写代码、创作内容等。每个会话都有独立的上下文，互不干扰。</p>
        </div>
        
        <!-- 消息列表 -->
        <div v-for="(message, index) in messages" :key="message.id || index" 
             class="message" :class="message.type">
          <!-- 用户消息 -->
          <div v-if="message.type === 'user'" class="user-message-wrapper">
            <!-- 编辑模式 -->
            <div v-if="editingMessageId === message.id" class="message-bubble user editing-bubble">
              <textarea
                v-model="editingMessageText"
                class="edit-textarea"
                @keydown.enter.exact.prevent="submitEditMessage(message.id, handleLogout)"
                @keydown.esc="cancelEditMessage"
                rows="1"
                ref="editTextareaRef"
              ></textarea>
              <div class="edit-actions">
                <span class="edit-hint">Enter 发送 · Shift+Enter 换行 · Esc 取消</span>
                <div class="edit-btns">
                  <button
                    class="edit-cancel-btn"
                    @click="cancelEditMessage"
                    :disabled="isLoading"
                  >取消</button>
                  <button
                    class="edit-submit-btn"
                    @click="submitEditMessage(message.id, handleLogout)"
                    :disabled="!editingMessageText.trim() || isLoading"
                  >发送 ➤</button>
                </div>
              </div>
            </div>
            <!-- 正常显示模式 -->
            <div v-else class="message-bubble user">
              <!-- 显示图片附件 -->
              <div v-if="message.files && message.files.length > 0" class="message-attachments">
                <div v-for="(file, idx) in message.files" :key="idx" class="attachment-item">
                  <img v-if="file.file_type === 'image'" :src="apiBaseUrl + file.url" class="message-image" />
                  <div v-else class="file-attachment">
                    <span class="file-icon">📄</span>
                    <span class="file-name">{{ file.filename }}</span>
                  </div>
                </div>
              </div>
              <div class="message-content">{{ getPlainText(message.content) }}</div>
              <div class="message-time">{{ message.time }}</div>
            </div>
            <!-- 鼠标悬停时出现的操作按钮 -->
            <div v-if="editingMessageId !== message.id" class="message-actions">
              <button
                class="msg-action-btn copy-msg-btn"
                :class="{ copied: copyTipMessageId === message.id }"
                @click.stop="copyMessage(message.id); showCopyTip(message.id)"
                :disabled="isLoading"
                :title="copyTipMessageId === message.id ? '已复制' : '复制'"
              >
                <svg v-if="copyTipMessageId !== message.id" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                </svg>
                <span v-else class="copied-text">✓</span>
              </button>
              <button
                class="msg-action-btn edit-msg-btn"
                @click.stop="startEditMessage(message.id)"
                :disabled="isLoading"
                title="编辑"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
              <button
                class="msg-action-btn delete-msg-btn"
                @click.stop="deleteMessage(message.id, handleLogout)"
                :disabled="isLoading"
                title="删除消息"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          </div>
          
          <!-- AI消息 -->
          <div v-else-if="message.type === 'assistant'" class="message-bubble assistant">
            <!-- 推理过程 (reasoning_content) -->
            <div v-if="message.reasoning_content" class="thinking-section">
              <div class="thinking-header" @click="message.showThinking = !message.showThinking">
                <span class="thinking-icon">💭</span>
                <span>推理过程</span>
                <span class="toggle-icon">{{ message.showThinking ? '▼' : '▶' }}</span>
              </div>
              <div v-show="message.showThinking" class="thinking-content">
                <pre>{{ message.reasoning_content }}</pre>
              </div>
            </div>
            
            <!-- 最终答案 -->
            <ContentRenderer :key="message.id + ':' + (message.isStreaming ? getPlainText(message.content).length : 'done')" :content="getPlainText(message.content)" :is-streaming="message.isStreaming" />
            
            <!-- 流式输出中指示 -->
            <span v-if="message.isStreaming" class="streaming-cursor">▊</span>
            <div class="message-time">{{ message.time }}</div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="isLoading && !currentAssistantMessage" class="loading-indicator">
          <span class="loading-dots">AI 正在生成</span>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="chat-input" ref="chatInputRef">
        <!-- 顶部拖拽拉宽手柄 -->
        <div class="resize-handle" @mousedown.prevent="startResize"></div>
        <!-- 已选文件预览 -->
        <div v-if="selectedFiles.length > 0" class="selected-files">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-tag">
            <span v-if="file.file_type === 'image'" class="file-icon">🖼️</span>
            <span v-else class="file-icon">📄</span>
            <span class="file-name">{{ file.filename }}</span>
            <button class="remove-file" @click="removeFile(index)">×</button>
          </div>
        </div>

        <!-- 第一行：输入框 -->
        <div class="input-row">
          <textarea
            v-model="newMessage"
            placeholder="今天帮你做些什么？"
            @keydown.enter.exact.prevent="sendMessage(handleLogout)"
            :disabled="isLoading || !currentSessionId"
            rows="1"
            ref="textareaRef"
            class="auto-resize-textarea"
          ></textarea>
        </div>

        <!-- 第二行：功能工具栏 - 固定在底部 -->
        <div class="toolbar-row">
          <!-- 左侧：模型选择 -->
          <div class="toolbar-left">
            <div class="model-selector" ref="modelSelectorRef">
              <div class="model-badge" @click.stop="toggleModelDropdown(handleLogout)">
                <span class="model-name">{{ getSelectedModelName() }}</span>
                <span class="model-arrow" :class="{ open: showModelDropdown }">▼</span>
              </div>
              <div v-if="showModelDropdown" class="model-dropdown">
                <div
                  v-for="model in models"
                  :key="model.id"
                  class="model-dropdown-item"
                  :class="{ active: model.id === selectedModelId }"
                  @click.stop="selectModel(model.id)"
                >
                  <span class="model-item-name">{{ model.model }}</span>
                </div>
                <div v-if="models.length === 0" class="model-dropdown-empty">
                  暂无可用模型
                </div>
              </div>
            </div>
          </div>

          <!-- 右侧：操作按钮区域 -->
          <div class="toolbar-right">
            <button
              class="toolbar-btn"
              @click="triggerFileUpload"
              :disabled="isLoading || !currentSessionId"
              title="上传文件"
            >
              +
            </button>
            <button
              class="toolbar-btn"
              title="语音输入"
              :disabled="isLoading"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="22"/>
              </svg>
            </button>
            <button
              class="toolbar-btn send-btn"
              v-if="!isLoading"
              @click="sendMessage(handleLogout)"
              :disabled="(!newMessage.trim() && selectedFiles.length === 0) || !currentSessionId"
            >
              ➤
            </button>
            <button
              class="toolbar-btn stop-btn"
              v-else
              @click="stopMessage"
              title="停止生成"
            >
              ■
            </button>
          </div>
        </div>

        <input
          ref="fileInput"
          type="file"
          style="display: none"
          accept="image/*,.txt,.md,.pdf,.json,.csv,.docx,.xlsx"
          @change="handleFileSelect"
          multiple
        />
      </div>
    </div>
  </div>
</template>

<script>
import { useChat } from './useChat.js'
import { API_CONFIG } from '../../utils/config.js'
import ContentRenderer from '../../components/ContentRenderer.vue'
import { THEMES, getSavedTheme, setTheme } from '../../themes/theme.js'

export default {
  name: 'Chat',
  components: { ContentRenderer },
  setup() {
    const chat = useChat()
    return {
      ...chat,
      apiBaseUrl: API_CONFIG.BASE_URL
    }
  },
  data() {
    return {
      userRole: localStorage.getItem('role') || 'user',
      showUserMenu: false,
      username: localStorage.getItem('username') || '用户',
      roleDisplay: this.getRoleDisplay(localStorage.getItem('role') || 'user'),
      copyTipMessageId: null,
      activeTheme: getSavedTheme(),
      showThemeSubmenu: false,
      THEMES
    }
  },
  computed: {
    isAdmin() {
      return ['admin', 'super_admin'].includes(this.userRole)
    }
  },
  mounted() {
    // 检查登录状态
    const token = localStorage.getItem('token');
    if (!token) {
      this.handleLogout();
      return;
    }
    this.loadSessions(this.handleLogout);
    this.loadModels(this.handleLogout);
    // textarea 自动高度
    this.$nextTick(() => {
      this.autoResizeTextarea();
    });
    // 点击外部关闭模型下拉
    document.addEventListener('click', this.closeModelDropdown);
  },
  beforeDestroy() {
    document.removeEventListener('click', this.closeModelDropdown);
  },
  methods: {
    getRoleDisplay(role) {
      const roleMap = {
        'user': '普通用户',
        'admin': '管理员',
        'super_admin': '超级管理员'
      }
      return roleMap[role] || '普通用户'
    },
    
    toggleUserMenu() {
      this.showUserMenu = !this.showUserMenu
      if (this.showUserMenu) {
        document.addEventListener('click', this.closeUserMenu)
      } else {
        document.removeEventListener('click', this.closeUserMenu)
      }
    },
    
    closeUserMenu(event) {
      const container = this.$el.querySelector('.user-menu-container')
      if (container && !container.contains(event.target)) {
        this.showUserMenu = false
        document.removeEventListener('click', this.closeUserMenu)
      }
    },
    
    changePassword() {
      this.showUserMenu = false
      alert('修改密码功能开发中')
    },

    showAccountSettings() {
      this.showUserMenu = false
      alert('账户设置功能开发中')
    },

    selectTheme(key) {
      this.activeTheme = setTheme(key)
      this.showThemeSubmenu = false
    },
    
    // 触发文件选择
    triggerFileUpload() {
      this.$refs.fileInput.click();
    },

    // 处理文件选择
    async handleFileSelect(event) {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      for (const file of files) {
        await this.uploadFile(file, this.handleLogout);
      }

      // 清空input，允许重复选择同一文件
      event.target.value = '';
    },

    // 滚动到底部
    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },

    handleLogout() {
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      localStorage.removeItem('role');
      this.$emit('logout');
    },

    goToAdmin() {
      this.$emit('go-admin');
    },

    renderTestChart() {
      // no-op
    },

    autoResizeTextarea() {
      const textarea = this.$refs.textareaRef;
      if (!textarea) return;
      textarea.style.height = 'auto';
      const newHeight = Math.min(textarea.scrollHeight, 200);
      textarea.style.height = newHeight + 'px';
    },

    startResize(e) {
      const inputEl = this.$refs.chatInputRef;
      if (!inputEl) return;
      const startHeight = inputEl.offsetHeight;
      const startY = e.clientY;
      const minHeight = 110;

      const onMove = (ev) => {
        const delta = startY - ev.clientY; // 向上拖为正
        const newHeight = Math.max(startHeight + delta, minHeight);
        inputEl.style.height = newHeight + 'px';
      };

      const onUp = () => {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
        // 拖拽结束后重新调整 textarea 高度
        this.autoResizeTextarea();
      };

      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    },

    closeModelDropdown(event) {
      const selector = this.$refs.modelSelectorRef;
      if (selector && !selector.contains(event.target)) {
        this.showModelDropdown = false;
      }
    },

    showCopyTip(messageId) {
      this.copyTipMessageId = messageId
      setTimeout(() => {
        if (this.copyTipMessageId === messageId) {
          this.copyTipMessageId = null
        }
      }, 1500)
    }
  },
  watch: {
    messages: {
      handler(newVal, oldVal) {
        // 仅在流式输出中或消息数量变化时才滚动到底部
        // 防止展开/收起推理过程等UI状态变化导致不必要的滚动
        if (this.isLoading || !oldVal || newVal.length !== oldVal.length) {
          this.scrollToBottom()
        }
      },
      deep: true
    },
    newMessage() {
      this.$nextTick(() => this.autoResizeTextarea());
    },
    editingMessageId() {
      if (this.editingMessageId) {
        this.$nextTick(() => {
          const ta = this.$refs.editTextareaRef
          if (ta) {
            // 可能是单个元素或数组（v-for 中）
            const el = Array.isArray(ta) ? ta[ta.length - 1] : ta
            if (el) {
              el.style.height = 'auto'
              el.style.height = Math.min(el.scrollHeight, 200) + 'px'
              el.focus()
            }
          }
        })
      }
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background-color: var(--app-bg);
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  min-width: 280px;
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
}

.sidebar:not(.sidebar-open) {
  margin-left: -280px;
}

.sidebar-header {
  padding: 14px 14px;
  border-bottom: 1px solid var(--sidebar-border);
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-chat-btn {
  flex: 1;
  padding: 10px 12px;
  background: var(--brand);
  color: var(--brand-fg);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.new-chat-btn:hover {
  background: var(--brand-hover);
  box-shadow: var(--shadow-btn);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 10px;
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
}

.session-list::-webkit-scrollbar { width: 6px; }
.session-list::-webkit-scrollbar-track { background: var(--scrollbar-track); }
.session-list::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 3px; }
.session-list::-webkit-scrollbar-button { display: none; }

.session-item {
  padding: 12px 14px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}

.session-item:hover { background-color: var(--card-border); }

.session-item.active { background-color: var(--brand-bg); }

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 60px;
}

.session-item.active .session-title { color: var(--brand-light); }

.session-meta {
  font-size: 11px;
  color: var(--text-placeholder);
  margin-top: 3px;
}

.session-actions {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.15s ease;
  background: var(--app-bg-secondary);
  border-radius: 6px;
  padding: 3px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.session-item:hover .session-actions { opacity: 1; }

.action-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.action-btn:hover { background: var(--card-border); }
.rename-btn:hover { color: var(--brand-light); }
.delete-btn:hover {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.15);
}

.rename-input-container { padding: 4px 40px 4px 0; }

.rename-input {
  width: 100%;
  padding: 5px 10px;
  border: 2px solid var(--brand);
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: var(--app-bg);
  color: var(--text-secondary);
  box-sizing: border-box;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--app-bg);
}

.chat-header {
  background: var(--header-bg);
  color: var(--text-primary);
  padding: 14px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid var(--header-border);
}

.menu-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-btn:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.06);
}

.chat-header h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
  letter-spacing: -0.2px;
}

/* 个人管理菜单 */
.user-menu-container { position: relative; }

.user-menu-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 20px;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.user-menu-btn:hover { background: rgba(255, 255, 255, 0.08); color: var(--text-primary); }

.user-menu-dropdown {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 8px;
  background: var(--dropdown-bg);
  border-radius: 12px;
  box-shadow: var(--shadow-dropdown);
  min-width: 200px;
  z-index: 1000;
  overflow: hidden;
  border: 1px solid var(--dropdown-border);
}

.user-info-header {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--app-bg);
  border-bottom: 1px solid var(--card-border);
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: var(--gradient-avatar);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
}

.user-details { display: flex; flex-direction: column; }
.user-name { font-weight: 600; color: var(--text-primary); font-size: 13px; }
.user-role { font-size: 11px; color: var(--text-muted); }

.menu-divider { border: none; height: 1px; background: var(--card-border); margin: 0; }

.user-menu-dropdown .menu-item {
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: left;
  transition: all 0.1s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-menu-dropdown .menu-item:hover { background: var(--card-border); color: var(--text-primary); }
.user-menu-dropdown .menu-item.logout-item:hover { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }

/* 主题选择 */
.menu-theme-section { border-top: none; }

.theme-expand-icon {
  font-size: 8px;
  color: var(--text-muted);
  margin-left: auto;
  transition: transform 0.2s ease;
}

.theme-expand-icon.open {
  transform: rotate(180deg);
}

.theme-inline-list {
  padding: 4px 16px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.theme-inline-item {
  padding: 8px 12px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  text-align: left;
  transition: all 0.12s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 6px;
}

.theme-inline-item:hover {
  background: var(--brand-bg);
  color: var(--text-primary);
}

.theme-inline-item.active {
  background: var(--brand-bg);
  color: var(--brand-light);
  font-weight: 600;
}

.theme-inline-icon {
  font-size: 14px;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
}

.chat-messages::-webkit-scrollbar { width: 6px; }
.chat-messages::-webkit-scrollbar-track { background: var(--scrollbar-track); }
.chat-messages::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 3px; }
.chat-messages::-webkit-scrollbar-button { display: none; }

.welcome-message { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.welcome-message h2 { margin: 0 0 12px 0; color: var(--text-primary); font-size: 20px; font-weight: 600; }
.welcome-message p { color: var(--text-placeholder); font-size: 14px; }

.message { display: flex; flex-direction: column; }

.message-bubble {
  max-width: 80%;
  padding: 14px 18px;
  border-radius: 16px;
  position: relative;
  word-wrap: break-word;
  line-height: 1.6;
}

.message-bubble.user {
  align-self: flex-end;
  background: var(--msg-bg-user);
  color: var(--text-primary);
  border: 1px solid var(--msg-border);
  border-bottom-right-radius: 6px;
}

.user-message-wrapper { display: flex; flex-direction: column; align-items: flex-end; position: relative; }

.message-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.user-message-wrapper:hover .message-actions { opacity: 1; }

.msg-action-btn {
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid var(--msg-border);
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  padding: 5px 7px;
  border-radius: 6px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.msg-action-btn:hover { background: rgba(255, 255, 255, 0.08); color: var(--text-secondary); }
.msg-action-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.delete-msg-btn:hover { color: #fca5a5; background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); }
.copy-msg-btn:hover { color: var(--brand-light); background: var(--brand-bg-hover); border-color: rgba(30, 80, 229, 0.3); }
.copy-msg-btn.copied { color: #4ade80; border-color: rgba(74, 222, 128, 0.3); }
.edit-msg-btn:hover { color: var(--brand-light); background: var(--brand-bg-hover); border-color: rgba(30, 80, 229, 0.3); }
.copied-text { font-size: 13px; font-weight: 600; }

/* 编辑模式样式 */
.editing-bubble { min-width: 280px; max-width: 90% !important; }
.edit-textarea {
  width: 100%;
  padding: 8px 10px;
  background: var(--app-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.5;
  resize: none;
  outline: none;
  min-height: 36px;
  max-height: 200px;
  box-sizing: border-box;
}
.edit-textarea:focus { border-color: var(--brand); box-shadow: var(--focus-ring); }

.edit-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; gap: 8px; }
.edit-hint { font-size: 11px; color: var(--text-placeholder); flex: 1; }
.edit-btns { display: flex; gap: 6px; flex-shrink: 0; }

.edit-cancel-btn {
  padding: 5px 14px;
  background: transparent;
  border: 1px solid var(--card-border);
  border-radius: 6px;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.edit-cancel-btn:hover { background: rgba(255, 255, 255, 0.06); color: var(--text-secondary); }

.edit-submit-btn {
  padding: 5px 14px;
  background: var(--brand);
  border: none;
  border-radius: 6px;
  color: var(--brand-fg);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}
.edit-submit-btn:hover:not(:disabled) { background: var(--brand-hover); }
.edit-submit-btn:disabled, .edit-cancel-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.message-bubble.assistant {
  align-self: flex-start;
  background: var(--msg-bg-assistant);
  color: var(--text-secondary);
  border: 1px solid var(--msg-border);
  border-bottom-left-radius: 6px;
  max-width: 90%;
}

.thinking-section { margin-bottom: 14px; border: 1px solid var(--card-border); border-radius: 8px; overflow: hidden; }
.thinking-header {
  background: var(--app-bg);
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
  user-select: none;
}
.thinking-header:hover { background: var(--card-bg); }
.thinking-content { padding: 12px; background: var(--app-bg); border-top: 1px solid var(--card-border); }
.thinking-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
  color: var(--text-placeholder);
  line-height: 1.5;
  font-family: ui-monospace, Consolas, monospace;
}

.answer-content { line-height: 1.65; font-size: 15px; }
.message-time { font-size: 11px; color: var(--text-placeholder); margin-top: 6px; text-align: right; }
.message-bubble.user .message-time { color: #475569; }

/* 消息附件 */
.message-attachments { margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 8px; }
.attachment-item { max-width: 200px; }
.message-image { max-width: 200px; max-height: 200px; border-radius: 8px; object-fit: cover; }
.file-attachment { display: flex; align-items: center; gap: 6px; padding: 6px 10px; background: rgba(255, 255, 255, 0.08); border-radius: 6px; font-size: 12px; }
.file-attachment .file-icon { font-size: 14px; }
.file-attachment .file-name { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.loading-indicator {
  align-self: flex-start;
  padding: 14px 18px;
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 16px;
  border-bottom-left-radius: 6px;
  font-size: 14px;
  color: var(--text-muted);
}

.loading-dots::after { content: ''; animation: dots 1.5s steps(4, end) infinite; }

.streaming-cursor {
  display: inline-block;
  color: var(--brand-glow);
  animation: blink 1s step-end infinite;
  margin-left: 2px;
}

@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
@keyframes dots { 0%, 20% { content: ''; } 40% { content: '.'; } 60% { content: '..'; } 80%, 100% { content: '...'; } }

/* 输入区域 */
.chat-input {
  position: relative;
  margin: 0 20px 16px;
  min-height: 110px;
  padding: 12px 14px 10px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.15);
}

.resize-handle { position: absolute; top: -2px; left: 10%; right: 10%; height: 6px; cursor: ns-resize; z-index: 1; }

.selected-files { display: flex; flex-wrap: wrap; gap: 6px; }
.file-tag { display: flex; align-items: center; gap: 6px; padding: 5px 10px; background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; font-size: 12px; color: var(--text-secondary); }
.file-icon { font-size: 13px; }
.file-name { max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.remove-file {
  background: none; border: none; color: var(--text-placeholder); cursor: pointer; font-size: 14px; padding: 0;
  width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; border-radius: 50%; transition: all 0.15s ease;
}
.remove-file:hover { background: rgba(255, 255, 255, 0.08); color: var(--text-secondary); }

.input-row { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; }
.input-row textarea {
  width: 100%; flex: 1; padding: 8px 4px; background: transparent; border: none; border-radius: 0;
  font-size: 14px; color: var(--text-primary); outline: none; font-family: inherit; box-sizing: border-box;
  resize: none; min-height: 24px; max-height: 200px; line-height: 1.5; overflow-y: auto;
}
.input-row textarea::placeholder { color: var(--text-placeholder); }
.input-row textarea:focus { box-shadow: none; }
.input-row textarea:disabled { opacity: 0.4; cursor: not-allowed; }

.toolbar-row { display: flex; align-items: center; justify-content: space-between; min-height: 32px; flex-shrink: 0; }
.toolbar-left { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }

.model-badge {
  display: flex; align-items: center; gap: 4px; padding: 4px 8px; background: transparent;
  border: none; border-radius: 8px; font-size: 13px; color: var(--text-muted);
  cursor: pointer; transition: all 0.15s ease; white-space: nowrap;
}
.model-badge:hover { background: rgba(255, 255, 255, 0.08); color: var(--text-secondary); }
.model-name { font-weight: 500; }
.model-arrow { font-size: 8px; color: #475569; margin-left: 2px; transition: transform 0.2s ease; }
.model-arrow.open { transform: rotate(180deg); }
.model-selector { position: relative; }

.model-dropdown {
  position: absolute; bottom: calc(100% + 8px); left: 0; min-width: 220px; max-height: 260px;
  overflow-y: auto; background: var(--dropdown-bg); border: 1px solid var(--dropdown-border);
  border-radius: 10px; box-shadow: var(--shadow-dropdown); z-index: 1001; padding: 4px;
  scrollbar-width: thin; scrollbar-color: var(--scrollbar-thumb) var(--scrollbar-track);
}
.model-dropdown::-webkit-scrollbar { width: 4px; }
.model-dropdown::-webkit-scrollbar-track { background: var(--scrollbar-track); }
.model-dropdown::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 2px; }

.model-dropdown-item {
  display: flex; align-items: center; justify-content: space-between; padding: 10px 12px;
  border-radius: 6px; cursor: pointer; transition: all 0.12s ease; font-size: 13px; color: var(--text-secondary);
}
.model-dropdown-item:hover { background: rgba(255, 255, 255, 0.08); color: var(--text-primary); }
.model-dropdown-item.active { background: var(--brand-bg); color: var(--brand-light); }
.model-item-name { font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.model-dropdown-empty { padding: 14px 12px; text-align: center; color: var(--text-placeholder); font-size: 13px; }

.toolbar-right { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.toolbar-btn {
  background: none; border: none; color: var(--text-placeholder); font-size: 18px;
  cursor: pointer; padding: 8px; border-radius: 8px; transition: all 0.15s ease;
  display: flex; align-items: center; justify-content: center; width: 36px; height: 36px;
}
.toolbar-btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.08); color: var(--text-secondary); }
.toolbar-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.toolbar-btn.send-btn { color: var(--brand); }
.toolbar-btn.send-btn:hover:not(:disabled) { background: var(--brand-bg-hover); color: var(--brand-glow); }

.toolbar-btn.stop-btn { color: #ef4444; font-size: 14px; animation: stopPulse 1.5s ease-in-out infinite; }
.toolbar-btn.stop-btn:hover { background: rgba(239, 68, 68, 0.15); color: #f87171; }

@keyframes stopPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed; left: 0; top: 0; bottom: 0; z-index: 100; margin-left: 0;
    transform: translateX(-100%); transition: transform 0.3s ease; box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
  }
  .sidebar.sidebar-open { transform: translateX(0); }
  .message-bubble { max-width: 90%; }
  .toolbar-row { flex-wrap: wrap; gap: 8px; }
  .toolbar-left { order: 2; }
  .toolbar-right { order: 1; }
  .input-row textarea { font-size: 13px; padding: 6px 2px; }
  .chat-input { margin: 0 12px 12px; }
}
</style>
