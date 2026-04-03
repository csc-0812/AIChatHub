import { ref, computed } from 'vue'
import * as chatApi from './chatApi.js'

export function useChat() {
  // 状态
  const sessions = ref([])
  const currentSessionId = ref(null)
  const currentSessionTitle = ref('')
  const messages = ref([])
  const newMessage = ref('')
  const isLoading = ref(false)
  const showSidebar = ref(true)
  const currentAssistantMessage = ref(null)
  const editingSessionId = ref(null)
  const editingTitle = ref('')
  const selectedFiles = ref([])

  // 计算属性
  const hasSessions = computed(() => sessions.value.length > 0)

  // 处理401/403未授权
  async function handleUnauthorized(response, onLogout) {
    if (response.status === 401) {
      let errorDetail = '登录已过期，请重新登录'
      try {
        const errorData = await response.json()
        if (errorData.detail && errorData.detail.includes('其他地方登录')) {
          errorDetail = '账号已在其他地方登录'
        }
      } catch (e) {}
      alert(errorDetail)
      onLogout?.()
      return true
    }
    if (response.status === 403) {
      alert('用户已被禁用，请联系管理员')
      onLogout?.()
      return true
    }
    return false
  }

  // 加载会话列表
  async function loadSessions(onLogout) {
    try {
      const data = await chatApi.getSessions()
      sessions.value = data.sessions

      // 如果有会话且没有当前会话，切换到第一个
      if (sessions.value.length > 0 && !currentSessionId.value) {
        await switchSession(sessions.value[0].session_id, onLogout)
      }
    } catch (error) {
      if (error.response && await handleUnauthorized(error.response, onLogout)) {
        return
      }
      console.error('加载会话列表失败:', error)
      throw error
    }
  }

  // 创建新会话
  async function createNewSession(onLogout) {
    try {
      const data = await chatApi.createSession()
      await loadSessions(onLogout)
      await switchSession(data.session_id, onLogout)
    } catch (error) {
      console.error('创建会话失败:', error)
      alert('创建会话失败')
      throw error
    }
  }

  // 切换会话
  async function switchSession(sessionId, onLogout) {
    currentSessionId.value = sessionId
    const session = sessions.value.find(s => s.session_id === sessionId)
    currentSessionTitle.value = session ? session.title : ''

    try {
      const data = await chatApi.getSession(sessionId)
      messages.value = data.messages.map(msg => ({
        type: msg.role,
        content: msg.content,
        time: new Date(msg.timestamp).toLocaleTimeString(),
        thinking: '',
        showThinking: false
      }))
    } catch (error) {
      if (error.response && await handleUnauthorized(error.response, onLogout)) {
        return
      }
      console.error('加载会话消息失败:', error)
      messages.value = []
    }

    // 移动端自动关闭侧边栏
    if (window.innerWidth <= 768) {
      showSidebar.value = false
    }
  }

  // 开始重命名
  function startRename(session) {
    editingSessionId.value = session.session_id
    editingTitle.value = session.title
  }

  // 确认重命名
  async function confirmRename(sessionId, onLogout) {
    if (!editingTitle.value.trim()) {
      cancelRename()
      return
    }

    const newTitle = editingTitle.value.trim()
    editingSessionId.value = null
    editingTitle.value = ''

    try {
      await chatApi.renameSession(sessionId, newTitle)
      await loadSessions(onLogout)
      // 如果重命名的是当前会话，更新标题
      if (currentSessionId.value === sessionId) {
        currentSessionTitle.value = newTitle
      }
    } catch (error) {
      console.error('重命名会话失败:', error)
      alert('重命名会话失败')
      throw error
    }
  }

  // 取消重命名
  function cancelRename() {
    editingSessionId.value = null
    editingTitle.value = ''
  }

  // 删除会话
  async function deleteSession(sessionId, onLogout) {
    if (!confirm('确定要删除这个会话吗？')) return

    try {
      await chatApi.deleteSession(sessionId)
      await loadSessions(onLogout)

      // 如果删除的是当前会话，切换到其他会话
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = null
        currentSessionTitle.value = ''
        messages.value = []
        if (sessions.value.length > 0) {
          await switchSession(sessions.value[0].session_id, onLogout)
        }
      }
    } catch (error) {
      console.error('删除会话失败:', error)
      alert('删除会话失败')
      throw error
    }
  }

  // 清空当前会话
  async function clearCurrentSession(onLogout) {
    if (!currentSessionId.value) return
    if (!confirm('确定要清空当前会话的所有消息吗？')) return

    try {
      await chatApi.clearSession(currentSessionId.value)
      messages.value = []
      await loadSessions(onLogout)
    } catch (error) {
      console.error('清空会话失败:', error)
      alert('清空会话失败')
      throw error
    }
  }

  // 上传文件
  async function uploadFile(file, onLogout) {
    try {
      const data = await chatApi.uploadFile(file)
      selectedFiles.value.push({
        file_id: data.file_id,
        filename: data.filename,
        file_type: data.file_type,
        content_type: data.content_type,
        size: data.size,
        url: data.url
      })
    } catch (error) {
      if (error.response && await handleUnauthorized(error.response, onLogout)) {
        return
      }
      console.error('文件上传错误:', error)
      alert('文件上传失败')
      throw error
    }
  }

  // 移除已选文件
  function removeFile(index) {
    selectedFiles.value.splice(index, 1)
  }

  // 发送消息
  async function sendMessage(onLogout) {
    if ((!newMessage.value.trim() && selectedFiles.value.length === 0) || 
        isLoading.value || !currentSessionId.value) return

    const userMessage = newMessage.value.trim()
    const filesToSend = [...selectedFiles.value]
    newMessage.value = ''
    selectedFiles.value = []

    // 构建消息内容（包含文件信息）
    let messageContent = userMessage
    if (filesToSend.length > 0) {
      const fileInfo = filesToSend.map(f => {
        if (f.file_type === 'image') {
          return `[图片: ${f.filename}]`
        } else {
          return `[文件: ${f.filename}]`
        }
      }).join('\n')
      messageContent = messageContent ? `${messageContent}\n${fileInfo}` : fileInfo
    }

    // 添加用户消息
    messages.value.push({
      type: 'user',
      content: messageContent,
      files: filesToSend,
      time: new Date().toLocaleTimeString()
    })

    isLoading.value = true

    // 创建AI消息占位
    currentAssistantMessage.value = {
      type: 'assistant',
      content: '',
      thinking: '',
      showThinking: true,
      time: new Date().toLocaleTimeString()
    }
    messages.value.push(currentAssistantMessage.value)

    try {
      const response = await chatApi.sendChatMessage(
        currentSessionId.value,
        userMessage
      )

      if (await handleUnauthorized(response, onLogout)) {
        messages.value.pop() // 移除AI消息占位
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // 读取SSE流
      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (let i = 0; i < lines.length; i++) {
          const line = lines[i]
          if (line.startsWith('event: ')) {
            const event = line.slice(7)
            const dataLine = lines[i + 1]
            if (dataLine && dataLine.startsWith('data: ')) {
              const data = JSON.parse(dataLine.slice(6))
              handleSSEEvent(event, data)
            }
          }
        }
      }

      // 更新会话列表
      await loadSessions(onLogout)

    } catch (error) {
      console.error('聊天错误:', error)
      currentAssistantMessage.value.content = '抱歉，发生了错误，请稍后重试。'
    } finally {
      isLoading.value = false
      currentAssistantMessage.value = null
    }
  }

  // 处理SSE事件
  function handleSSEEvent(event, data) {
    if (!currentAssistantMessage.value) return

    switch (event) {
      case 'session_created':
        currentSessionId.value = data.session_id
        currentSessionTitle.value = data.title
        break

      case 'start':
        console.log('开始生成:', data)
        break

      case 'thinking':
        currentAssistantMessage.value.thinking = data.content
        break

      case 'thinking_chunk':
        currentAssistantMessage.value.thinking += data.chunk
        break

      case 'answer':
        currentAssistantMessage.value.content = data.content
        break

      case 'answer_chunk':
        currentAssistantMessage.value.content += data.chunk
        break

      case 'done':
        if (data.thinking) {
          currentAssistantMessage.value.thinking = data.thinking
        }
        if (data.answer) {
          currentAssistantMessage.value.content = data.answer
        }
        break

      case 'error':
        console.error('SSE错误:', data)
        currentAssistantMessage.value.content = '抱歉，发生了错误：' + data.message
        break
    }
  }

  // 切换侧边栏
  function toggleSidebar() {
    showSidebar.value = !showSidebar.value
  }

  // 格式化日期
  function formatDate(dateString) {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now - date

    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000)
      return minutes < 1 ? '刚刚' : `${minutes}分钟前`
    }

    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000)
      return `${hours}小时前`
    }

    return date.toLocaleDateString()
  }

  return {
    // 状态
    sessions,
    currentSessionId,
    currentSessionTitle,
    messages,
    newMessage,
    isLoading,
    showSidebar,
    currentAssistantMessage,
    editingSessionId,
    editingTitle,
    selectedFiles,
    // 计算属性
    hasSessions,
    // 方法
    loadSessions,
    createNewSession,
    switchSession,
    startRename,
    confirmRename,
    cancelRename,
    deleteSession,
    clearCurrentSession,
    uploadFile,
    removeFile,
    sendMessage,
    toggleSidebar,
    formatDate
  }
}
