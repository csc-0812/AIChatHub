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
  const currentAssistantMessageId = ref(null)  // 参考IFA: 当前流式输出的临时消息ID
  const editingSessionId = ref(null)
  const editingTitle = ref('')
  const selectedFiles = ref([])
  const abortController = ref(null)     // 用于取消正在进行的流式请求
  // 模型选择
  const models = ref([])               // 可用模型列表
  const selectedModelId = ref(null)    // 当前选中的模型ID
  const showModelDropdown = ref(false) // 模型下拉是否展示

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
        id: msg.id,
        type: msg.role,
        content: normalizeContent(msg.content),
        reasoning_content: msg.reasoning_content || '',
        showThinking: false,  // 历史消息默认收起推理过程
        isStreaming: false,
        time: new Date(msg.timestamp).toLocaleTimeString()
      }))
      // 恢复该会话之前使用的模型
      if (data.model_id) {
        const modelExists = models.value.some(m => m.id === data.model_id)
        if (modelExists) {
          selectedModelId.value = data.model_id
        }
      }
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

  /**
   * 规范化 content 格式
   * 参考IFA: content 始终为数组 [{kind: "texts"/"files"/"images", ...}]
   * 同时兼容旧的字符串格式
   */
  function normalizeContent(content) {
    if (!content) return [{ kind: 'texts', texts: [''] }]
    if (Array.isArray(content)) return content
    // 旧格式：字符串 → 转换为结构化格式
    return [{ kind: 'texts', texts: [content] }]
  }

  /**
   * 从结构化 content 中提取纯文本
   */
  function getPlainText(content) {
    if (!content) return ''
    if (typeof content === 'string') return content
    if (!Array.isArray(content)) return ''
    return content
      .filter(block => block.kind === 'texts' && block.texts)
      .flatMap(block => block.texts)
      .join('\n')
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

    // 参考IFA: 使用临时ID，等待后端 update_user_message 回传真实ID
    const tempUserId = `temp-${Date.now()}`
    messages.value.push({
      id: tempUserId,
      type: 'user',
      content: [{ kind: 'texts', texts: [messageContent] }],
      files: filesToSend,
      reasoning_content: '',
      isStreaming: false,
      showThinking: false,
      time: new Date().toLocaleTimeString()
    })

    isLoading.value = true
    
    // 创建 AbortController，用于支持手动停止
    abortController.value = new AbortController()

    // 参考IFA: 创建AI消息占位，使用临时ID
    const tempAiId = `temp-${Date.now() + 1}`
    currentAssistantMessageId.value = tempAiId
    currentAssistantMessage.value = {
      id: tempAiId,
      type: 'assistant',
      content: [{ kind: 'texts', texts: [''] }],
      reasoning_content: '',
      showThinking: true,
      isStreaming: true,
      time: new Date().toLocaleTimeString()
    }
    messages.value.push(currentAssistantMessage.value)

    try {
      const response = await chatApi.sendChatMessage(
        currentSessionId.value,
        userMessage,
        abortController.value.signal,
        selectedModelId.value
      )

      if (await handleUnauthorized(response, onLogout)) {
        messages.value.pop() // 移除AI消息占位
        return
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // 参考IFA: fetch + ReadableStream SSE 解析
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        // 参考IFA: 按 \n\n 分隔事件，最后一个可能不完整暂存buffer
        while (buffer.includes('\n\n')) {
          const eventEndIdx = buffer.indexOf('\n\n')
          const eventString = buffer.slice(0, eventEndIdx)
          buffer = buffer.slice(eventEndIdx + 2)
          
          parseAndHandleSSEEvent(eventString)
        }
      }

      // 处理缓冲区可能残留的最后一个事件
      if (buffer.trim()) {
        parseAndHandleSSEEvent(buffer)
      }

      // 更新会话列表
      await loadSessions(onLogout)

    } catch (error) {
      const targetMsg = _getCurrentAssistantMsg()
      if (error.name === 'AbortError') {
        // 用户手动停止
        if (targetMsg) {
          const text = getPlainText(targetMsg.content)
          if (!text) {
            targetMsg.content = [{ kind: 'texts', texts: ['（已停止生成）'] }]
          } else {
            const currentTexts = targetMsg.content[0].texts
            targetMsg.content[0].texts = [...currentTexts, '\n\n*（已停止生成）*']
          }
          targetMsg.isStreaming = false
        }
      } else {
        console.error('聊天错误:', error)
        if (targetMsg) {
          targetMsg.content = [{ kind: 'texts', texts: ['抱歉，发生了错误，请稍后重试。'] }]
          targetMsg.isStreaming = false
        }
      }
    } finally {
      isLoading.value = false
      abortController.value = null
      currentAssistantMessageId.value = null
      currentAssistantMessage.value = null
    }
  }

  // 手动停止正在进行的流式输出
  function stopMessage() {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
  }

  // 参考IFA: 解析 SSE 事件字符串
  function parseAndHandleSSEEvent(eventString) {
    let eventType = ''
    const dataLines = []

    for (const line of eventString.split('\n')) {
      const colonIndex = line.indexOf(':')
      if (colonIndex === -1) continue

      const field = line.slice(0, colonIndex)
      let value = line.slice(colonIndex + 1)
      if (value.startsWith(' ')) value = value.slice(1)  // SSE规范：去掉首空格

      if (field === 'event') eventType = value
      else if (field === 'data') dataLines.push(value)
    }

    if (eventType && dataLines.length > 0) {
      try {
        const dataStr = dataLines.join('\n')
        const data = JSON.parse(dataStr)
        handleSSEEvent(eventType, data)
      } catch (e) {
        console.error('SSE JSON 解析失败:', e, dataLines.join('\n'))
      }
    }
  }

  /**
   * 获取当前流式输出中的助手消息（通过ID在 messages 数组中查找）
   * 确保始终操作 messages 数组中的响应式对象，避免引用不同步问题
   */
  function _getCurrentAssistantMsg() {
    if (!currentAssistantMessageId.value) return null
    return messages.value.find(m => m.id === currentAssistantMessageId.value) || null
  }

  /**
   * 处理SSE事件
   * 参考IFA: 事件类型包括
   *   update_user_message → reasoning_content_chunk → content_chunk
   *   → update_assistant_message → done
   */
  function handleSSEEvent(event, data) {
    // 除 session_created / update_user_message 外，统一通过 ID 查找目标消息
    let targetMsg = null
    switch (event) {
      case 'session_created':
        currentSessionId.value = data.session_id
        currentSessionTitle.value = data.title
        break

      case 'update_user_message':
        // 参考IFA: 用后端返回的真实ID替换用户消息的临时ID
        if (data.id) {
          const userMsg = messages.value.find(m => m.type === 'user' && m.id.startsWith('temp-'))
          if (userMsg) {
            userMsg.id = data.id
          }
        }
        break

      case 'reasoning_content_chunk':
        // 参考IFA: 推理内容逐块追加到助手消息
        targetMsg = _getCurrentAssistantMsg()
        if (!targetMsg) return
        if (!targetMsg.reasoning_content) {
          targetMsg.reasoning_content = ''
        }
        targetMsg.reasoning_content += data
        break

      case 'content_chunk':
        // 参考IFA: 同类型 chunk 合并（texts 合并 texts）
        targetMsg = _getCurrentAssistantMsg()
        if (!targetMsg) return
        _mergeContentChunk(targetMsg.content, data)
        break

      case 'update_assistant_message':
        // 参考IFA: 用真实ID替换临时ID，标记流式结束
        targetMsg = _getCurrentAssistantMsg()
        if (!targetMsg) return
        targetMsg.id = data.id
        targetMsg.content = normalizeContent(data.content)
        if (data.reasoning_content) {
          targetMsg.reasoning_content = data.reasoning_content
        }
        targetMsg.isStreaming = false
        targetMsg.showThinking = false  // 回复完毕，收起推理过程
        break

      case 'done':
        // 参考IFA: 流式输出完成，收起推理过程
        targetMsg = _getCurrentAssistantMsg()
        if (targetMsg) {
          targetMsg.isStreaming = false
          targetMsg.showThinking = false
        }
        break

      case 'error':
        console.error('SSE错误:', data)
        targetMsg = _getCurrentAssistantMsg()
        if (targetMsg) {
          targetMsg.content = [{ kind: 'texts', texts: ['抱歉，发生了错误：' + data.message] }]
          targetMsg.isStreaming = false
          targetMsg.showThinking = false
        }
        break

      // 向后兼容旧版事件类型
      case 'start':
        console.log('开始生成:', data)
        break

      case 'thinking':
        targetMsg = _getCurrentAssistantMsg()
        if (targetMsg) {
          targetMsg.reasoning_content = data.content
        }
        break

      case 'thinking_chunk':
        targetMsg = _getCurrentAssistantMsg()
        if (targetMsg) {
          if (!targetMsg.reasoning_content) {
            targetMsg.reasoning_content = ''
          }
          targetMsg.reasoning_content += data.chunk
        }
        break

      case 'answer':
        targetMsg = _getCurrentAssistantMsg()
        if (targetMsg) {
          targetMsg.content = [{ kind: 'texts', texts: [data.content] }]
        }
        break

      case 'answer_chunk':
        targetMsg = _getCurrentAssistantMsg()
        if (targetMsg) {
          const texts = targetMsg.content[0]?.texts || ['']
          texts[texts.length - 1] += data.chunk
        }
        break
    }
  }

  /**
   * 参考IFA: 合并结构化 content chunk
   * 同类型 chunk 合并数组（texts → texts, files → files）
   * 创建新引用触发 Vue 响应式
   */
  function _mergeContentChunk(existingContent, newChunk) {
    if (!newChunk || !newChunk.kind) return

    // 找到同类型块
    let existingBlock = existingContent.find(b => b.kind === newChunk.kind)
    
    if (existingBlock) {
      if (newChunk.kind === 'texts' && newChunk.texts) {
        existingBlock.texts = [...(existingBlock.texts || []), ...newChunk.texts]
      } else if (newChunk.kind === 'files' && newChunk.files) {
        existingBlock.files = [...(existingBlock.files || []), ...newChunk.files]
      } else if (newChunk.kind === 'images' && newChunk.images) {
        existingBlock.images = [...(existingBlock.images || []), ...newChunk.images]
      }
      // 创建新引用触发 Vue 响应式
      existingBlock = { ...existingBlock }
      const idx = existingContent.findIndex(b => b.kind === newChunk.kind)
      if (idx >= 0) {
        existingContent.splice(idx, 1, existingBlock)
      }
    } else {
      // 新类型，直接添加
      existingContent.push({
        kind: newChunk.kind,
        texts: newChunk.texts ? [...newChunk.texts] : [],
        files: newChunk.files ? [...newChunk.files] : [],
        images: newChunk.images ? [...newChunk.images] : []
      })
    }
  }

  // 切换侧边栏
  function toggleSidebar() {
    showSidebar.value = !showSidebar.value
  }

  // 加载模型列表
  async function loadModels(onLogout) {
    try {
      const data = await chatApi.getModelList()
      models.value = data.models || []
      
      // 首次加载时初始化选中模型
      if (!selectedModelId.value && models.value.length > 0) {
        selectedModelId.value = models.value[0].id
      }
      // 刷新后如果当前选中模型已不在列表中，回退到第一个
      if (selectedModelId.value && !models.value.some(m => m.id === selectedModelId.value)) {
        selectedModelId.value = models.value.length > 0 ? models.value[0].id : null
      }
    } catch (error) {
      if (error.response && await handleUnauthorized(error.response, onLogout)) {
        return
      }
      console.error('加载模型列表失败:', error)
    }
  }

  // 切换模型下拉（打开时刷新列表）
  async function toggleModelDropdown(onLogout) {
    showModelDropdown.value = !showModelDropdown.value
    if (showModelDropdown.value) {
      await loadModels(onLogout)
    }
  }

  // 切换模型
  function selectModel(modelId) {
    selectedModelId.value = modelId
    showModelDropdown.value = false
  }

  // 获取当前选中模型名称（显示 model 字段，如 gpt-4o）
  function getSelectedModelName() {
    const model = models.value.find(m => m.id === selectedModelId.value)
    return model ? model.model : '默认模型'
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
    currentAssistantMessageId,
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
    stopMessage,
    toggleSidebar,
    formatDate,
    getPlainText,
    normalizeContent,
    // 模型选择
    models,
    selectedModelId,
    showModelDropdown,
    loadModels,
    toggleModelDropdown,
    selectModel,
    getSelectedModelName
  }
}
