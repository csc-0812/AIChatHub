<template>
  <div class="chat-container">
    <!-- 侧边栏 - 会话列表 -->
    <div class="sidebar" :class="{ 'sidebar-open': showSidebar }">
      <div class="sidebar-header">
        <h2>会话列表</h2>
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
      
      <div class="sidebar-footer">
        <button v-if="isAdmin" class="admin-btn" @click="goToAdmin">
          ⚙️ 管理控制台
        </button>
        <button class="logout-btn" @click="handleLogout">
          退出登录
        </button>
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
        <button 
          class="clear-btn" 
          @click="clearCurrentSession(handleLogout)"
          :disabled="!currentSessionId"
          title="清空当前会话"
        >
          清空
        </button>
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
            <div class="answer-content">{{ message.content }}</div>
            <div class="message-time">{{ message.time }}</div>
          </div>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="isLoading" class="loading-indicator">
          <span class="loading-dots">AI 正在思考</span>
        </div>
      </div>
      
      <!-- 输入区域 -->
      <div class="chat-input">
        <!-- 已选文件预览 -->
        <div v-if="selectedFiles.length > 0" class="selected-files">
          <div v-for="(file, index) in selectedFiles" :key="index" class="file-tag">
            <span v-if="file.file_type === 'image'" class="file-icon">🖼️</span>
            <span v-else class="file-icon">📄</span>
            <span class="file-name">{{ file.filename }}</span>
            <button class="remove-file" @click="removeFile(index)">×</button>
          </div>
        </div>
        
        <div class="input-row">
          <!-- 文件上传按钮 -->
          <button 
            class="upload-btn" 
            @click="triggerFileUpload"
            :disabled="isLoading || !currentSessionId"
            title="上传文件或图片"
          >
            📎
          </button>
          <input 
            ref="fileInput"
            type="file" 
            style="display: none"
            accept="image/*,.txt,.md,.pdf,.json,.csv,.docx,.xlsx"
            @change="handleFileSelect"
            multiple
          />
          
          <input 
            type="text" 
            v-model="newMessage" 
            placeholder="输入消息..." 
            @keyup.enter="sendMessage(handleLogout)"
            :disabled="isLoading || !currentSessionId"
          />
          <button 
            class="send-button" 
            @click="sendMessage(handleLogout)" 
            :disabled="isLoading || (!newMessage.trim() && selectedFiles.length === 0) || !currentSessionId"
          >
            {{ isLoading ? '发送中...' : '发送' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useChat } from './useChat.js'
import { API_CONFIG } from '../../utils/config.js'

export default {
  name: 'Chat',
  setup() {
    const chat = useChat()
    return {
      ...chat,
      apiBaseUrl: API_CONFIG.BASE_URL
    }
  },
  data() {
    return {
      userRole: localStorage.getItem('role') || 'user'
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
  },
  methods: {
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
    }
  },
  watch: {
    messages: {
      handler() {
        this.scrollToBottom();
      },
      deep: true
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background-color: #f5f5f5;
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  background-color: #fff;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.sidebar-header h2 {
  margin: 0 0 15px 0;
  font-size: 18px;
  color: #333;
}

.new-chat-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.new-chat-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.session-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
}

.session-item:hover {
  background-color: #f5f5f5;
}

.session-item.active {
  background-color: #e8eaff;
  border-left: 3px solid #667eea;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-right: 60px; /* 为操作按钮留出空间 */
}

.session-meta {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.session-actions {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
  background-color: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 4px;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 14px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.rename-btn:hover {
  color: #667eea;
}

.delete-btn:hover {
  color: #f44336;
}

.rename-input-container {
  padding: 4px 40px 4px 0;
}

.rename-input {
  width: 100%;
  padding: 6px 10px;
  border: 2px solid #667eea;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  background-color: white;
  color: #333;
  box-sizing: border-box;
}

.sidebar-footer {
  padding: 15px;
  border-top: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.admin-btn {
  width: 100%;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.admin-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.logout-btn {
  width: 100%;
  padding: 10px;
  background-color: #f5f5f5;
  color: #666;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s ease;
}

.logout-btn:hover {
  background-color: #e0e0e0;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.menu-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  display: none;
}

.chat-header h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  flex: 1;
}

.clear-btn {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s ease;
}

.clear-btn:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.3);
}

.clear-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.welcome-message h2 {
  margin: 0 0 15px 0;
  color: #333;
}

.message {
  display: flex;
  flex-direction: column;
}

.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  position: relative;
  word-wrap: break-word;
}

.message-bubble.user {
  align-self: flex-end;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  align-self: flex-start;
  background-color: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.thinking-section {
  margin-bottom: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.thinking-header {
  background-color: #f8f9fa;
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
  user-select: none;
}

.thinking-header:hover {
  background-color: #e9ecef;
}

.thinking-icon {
  font-size: 16px;
}

.toggle-icon {
  margin-left: auto;
  font-size: 12px;
}

.thinking-content {
  padding: 12px;
  background-color: #f8f9fa;
  border-top: 1px solid #e0e0e0;
}

.thinking-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
  color: #555;
  line-height: 1.5;
}

.answer-content {
  line-height: 1.6;
  font-size: 15px;
}

.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 6px;
  text-align: right;
}

.message-bubble.user .message-time {
  color: rgba(255, 255, 255, 0.8);
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
  padding: 8px 12px;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font-size: 13px;
}

.file-attachment .file-icon {
  font-size: 16px;
}

.file-attachment .file-name {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.loading-indicator {
  align-self: flex-start;
  padding: 12px 16px;
  background-color: white;
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

/* 输入区域 */
.chat-input {
  padding: 15px 20px;
  background-color: white;
  border-top: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.selected-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-bottom: 5px;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: #f0f0f0;
  border-radius: 16px;
  font-size: 13px;
  color: #555;
}

.file-icon {
  font-size: 14px;
}

.file-name {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-file {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.remove-file:hover {
  background-color: #e0e0e0;
  color: #666;
}

.input-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.upload-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.upload-btn:hover:not(:disabled) {
  background-color: #f0f0f0;
}

.upload-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chat-input input[type="text"] {
  flex: 1;
  padding: 12px 18px;
  border: 2px solid #e0e0e0;
  border-radius: 25px;
  font-size: 15px;
  outline: none;
  transition: all 0.3s ease;
}

.chat-input input[type="text"]:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.chat-input input[type="text"]:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.send-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 25px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.send-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 100;
    transform: translateX(-100%);
  }
  
  .sidebar.sidebar-open {
    transform: translateX(0);
  }
  
  .menu-btn {
    display: block;
  }
  
  .message-bubble {
    max-width: 90%;
  }
}
</style>
