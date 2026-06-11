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
        <div v-for="(message, index) in messages" :key="index" 
             class="message" :class="message.type">
          <!-- 用户消息 -->
          <div v-if="message.type === 'user'" class="message-bubble user">
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
            <div class="message-content">{{ message.content }}</div>
            <div class="message-time">{{ message.time }}</div>
          </div>
          
          <!-- AI消息 -->
          <div v-else-if="message.type === 'assistant'" class="message-bubble assistant">
            <!-- 思考过程 -->
            <div v-if="message.thinking" class="thinking-section">
              <div class="thinking-header" @click="message.showThinking = !message.showThinking">
                <span class="thinking-icon">💭</span>
                <span>思考过程</span>
                <span class="toggle-icon">{{ message.showThinking ? '▼' : '▶' }}</span>
              </div>
              <div v-show="message.showThinking" class="thinking-content">
                <pre>{{ message.thinking }}</pre>
              </div>
            </div>
            
            <!-- 最终答案 -->
            <ContentRenderer :content="message.content" />
            <div class="message-time">{{ message.time }}</div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-indicator">
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
            <div class="model-badge">
              <span class="model-name">deepseek-v4-pro</span>
              <span class="model-arrow">▼</span>
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
      roleDisplay: this.getRoleDisplay(localStorage.getItem('role') || 'user')
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
    // textarea 自动高度
    this.$nextTick(() => {
      this.autoResizeTextarea();
    });
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
    }
  },
  watch: {
    messages: {
      handler() {
        this.scrollToBottom()
      },
      deep: true
    },
    newMessage() {
      this.$nextTick(() => this.autoResizeTextarea());
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background-color: #0f172a;
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  min-width: 280px;
  background-color: #1e293b;
  border-right: 1px solid #334155;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
}

.sidebar:not(.sidebar-open) {
  margin-left: -280px;
}

.sidebar-header {
  padding: 14px 14px;
  border-bottom: 1px solid #334155;
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-chat-btn {
  flex: 1;
  padding: 10px 12px;
  background: #d97706;
  color: white;
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
  background: #b45309;
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.25);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 10px;
  scrollbar-width: thin;
  scrollbar-color: #334155 transparent;
}

.session-list::-webkit-scrollbar {
  width: 6px;
}

.session-list::-webkit-scrollbar-track {
  background: transparent;
}

.session-list::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 3px;
}

.session-list::-webkit-scrollbar-button {
  display: none;
}

.session-item {
  padding: 12px 14px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  transition: all 0.15s ease;
}

.session-item:hover {
  background-color: #334155;
}

.session-item.active {
  background-color: rgba(217, 119, 6, 0.12);
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 60px;
}

.session-item.active .session-title {
  color: #fbbf24;
}

.session-meta {
  font-size: 11px;
  color: #64748b;
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
  background: rgba(30, 41, 59, 0.95);
  border-radius: 6px;
  padding: 3px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.session-item:hover .session-actions {
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: #334155;
}

.rename-btn:hover {
  color: #fbbf24;
}

.delete-btn:hover {
  color: #fca5a5;
  background: rgba(239, 68, 68, 0.15);
}

.rename-input-container {
  padding: 4px 40px 4px 0;
}

.rename-input {
  width: 100%;
  padding: 5px 10px;
  border: 2px solid #d97706;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  background: #0f172a;
  color: #e2e8f0;
  box-sizing: border-box;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #0f172a;
}

.chat-header {
  background: #0f172a;
  color: #f1f5f9;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border-bottom: 1px solid #1e293b;
}

.menu-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-btn:hover {
  color: #f1f5f9;
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
.user-menu-container {
  position: relative;
}

.user-menu-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  transition: all 0.15s ease;
}

.user-menu-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #f1f5f9;
}

.user-menu-dropdown {
  position: absolute;
  right: 0;
  top: 100%;
  margin-top: 8px;
  background: #1e293b;
  border-radius: 12px;
  box-shadow:
    0 1px 2px rgba(0, 0, 0, 0.2),
    0 8px 32px rgba(0, 0, 0, 0.3);
  min-width: 200px;
  z-index: 1000;
  overflow: hidden;
  border: 1px solid #334155;
}

.user-info-header {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: #0f172a;
  border-bottom: 1px solid #334155;
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: #d97706;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
}

.user-details {
  display: flex;
  flex-direction: column;
}

.user-name {
  font-weight: 600;
  color: #f1f5f9;
  font-size: 13px;
}

.user-role {
  font-size: 11px;
  color: #94a3b8;
}

.menu-divider {
  border: none;
  height: 1px;
  background: #334155;
  margin: 0;
}

.user-menu-dropdown .menu-item {
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  color: #cbd5e1;
  text-align: left;
  transition: all 0.1s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-menu-dropdown .menu-item:hover {
  background: #334155;
  color: #f1f5f9;
}

.user-menu-dropdown .menu-item.logout-item:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
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
  scrollbar-color: #334155 transparent;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-button {
  display: none;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.welcome-message h2 {
  margin: 0 0 12px 0;
  color: #f1f5f9;
  font-size: 20px;
  font-weight: 600;
}

.welcome-message p {
  color: #64748b;
  font-size: 14px;
}

.message {
  display: flex;
  flex-direction: column;
}

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
  background: #1e293b;
  color: #f1f5f9;
  border: 1px solid #334155;
  border-bottom-right-radius: 6px;
}

.message-bubble.assistant {
  align-self: flex-start;
  background: #1e293b;
  color: #e2e8f0;
  border: 1px solid #334155;
  border-bottom-left-radius: 6px;
  max-width: 90%;
}

.thinking-section {
  margin-bottom: 14px;
  border: 1px solid #334155;
  border-radius: 8px;
  overflow: hidden;
}

.thinking-header {
  background: #0f172a;
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
  user-select: none;
}

.thinking-header:hover {
  background: #1e293b;
}

.thinking-icon {
  font-size: 14px;
}

.toggle-icon {
  margin-left: auto;
  font-size: 10px;
}

.thinking-content {
  padding: 12px;
  background: #0f172a;
  border-top: 1px solid #334155;
}

.thinking-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  font-family: ui-monospace, Consolas, monospace;
}

.answer-content {
  line-height: 1.65;
  font-size: 15px;
}

.message-time {
  font-size: 11px;
  color: #64748b;
  margin-top: 6px;
  text-align: right;
}

.message-bubble.user .message-time {
  color: #475569;
}

/* 消息附件 */
.message-attachments {
  margin-bottom: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.attachment-item {
  max-width: 200px;
}

.message-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 8px;
  object-fit: cover;
}

.file-attachment {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  font-size: 12px;
}

.file-attachment .file-icon {
  font-size: 14px;
}

.file-attachment .file-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-indicator {
  align-self: flex-start;
  padding: 14px 18px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  border-bottom-left-radius: 6px;
  font-size: 14px;
  color: #94a3b8;
}

.loading-dots::after {
  content: '';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% { content: ''; }
  40% { content: '.'; }
  60% { content: '..'; }
  80%, 100% { content: '...'; }
}

/* 输入区域 - 单卡片式统一风格 */
.chat-input {
  position: relative;
  margin: 0 20px 16px;
  min-height: 110px;
  padding: 12px 14px 10px;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 0 8px rgba(0, 0, 0, 0.15);
}

/* 顶部拖拽拉宽手柄 - 靠近上沿时显示可拉宽光标 */
.resize-handle {
  position: absolute;
  top: -2px;
  left: 10%;
  right: 10%;
  height: 6px;
  cursor: ns-resize;
  z-index: 1;
}

.selected-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  font-size: 12px;
  color: #cbd5e1;
}

.file-icon {
  font-size: 13px;
}

.file-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.15s ease;
}

.remove-file:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

/* 第一行：输入框 - 占据剩余空间 */
.input-row {
  width: 100%;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.input-row textarea {
  width: 100%;
  flex: 1;
  padding: 8px 4px;
  background: transparent;
  border: none;
  border-radius: 0;
  font-size: 14px;
  color: #f1f5f9;
  outline: none;
  font-family: inherit;
  box-sizing: border-box;
  resize: none;
  min-height: 24px;
  max-height: 200px;
  line-height: 1.5;
  overflow-y: auto;
}

.input-row textarea::placeholder {
  color: #64748b;
}

.input-row textarea:focus {
  box-shadow: none;
}

.input-row textarea:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* 第二行：功能工具栏 - 固定底部 */
.toolbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 32px;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.model-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.model-badge:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
}

.model-name {
  font-weight: 500;
}

.model-arrow {
  font-size: 8px;
  color: #475569;
  margin-left: 2px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.toolbar-btn {
  background: none;
  border: none;
  color: #64748b;
  font-size: 18px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
}

.toolbar-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.toolbar-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.toolbar-btn.send-btn {
  color: #d97706;
}

.toolbar-btn.send-btn:hover:not(:disabled) {
  background: rgba(217, 119, 6, 0.15);
  color: #fbbf24;
}

.toolbar-btn.stop-btn {
  color: #ef4444;
  font-size: 14px;
  animation: stopPulse 1.5s ease-in-out infinite;
}

.toolbar-btn.stop-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

@keyframes stopPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    margin-left: 0;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
  }

  .sidebar.sidebar-open {
    transform: translateX(0);
  }

  .message-bubble {
    max-width: 90%;
  }

  .toolbar-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .toolbar-left {
    order: 2;
  }

  .toolbar-right {
    order: 1;
  }

  .input-row textarea {
    font-size: 13px;
    padding: 6px 2px;
  }

  .chat-input {
    margin: 0 12px 12px;
  }
}
</style>
