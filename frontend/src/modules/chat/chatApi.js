/**
 * 聊天模块 API 服务
 * 处理所有与聊天相关的 API 请求
 */

import { API_CONFIG } from '../../utils/config.js'

const API_BASE_URL = API_CONFIG.API_BASE_URL

function getToken() {
  return localStorage.getItem('token')
}

async function request(url, options = {}) {
  const token = getToken()
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  }
  
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers
    }
  })
  
  return response
}

/**
 * 创建新会话
 */
export async function createSession(title = null, maxContextLength = 10) {
  const response = await request('/chat/sessions', {
    method: 'POST',
    body: JSON.stringify({
      title,
      max_context_length: maxContextLength
    })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '创建会话失败')
  }
  
  return response.json()
}

/**
 * 获取会话列表
 */
export async function getSessions() {
  const response = await request('/chat/sessions')
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '获取会话列表失败')
  }
  
  return response.json()
}

/**
 * 获取会话详情
 */
export async function getSession(sessionId) {
  const response = await request(`/chat/sessions/${sessionId}`)
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '获取会话详情失败')
  }
  
  return response.json()
}

/**
 * 删除会话
 */
export async function deleteSession(sessionId) {
  const response = await request(`/chat/sessions/${sessionId}`, {
    method: 'DELETE'
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '删除会话失败')
  }
  
  return response.json()
}

/**
 * 清空会话消息
 */
export async function clearSession(sessionId) {
  const response = await request(`/chat/sessions/${sessionId}/clear`, {
    method: 'POST'
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '清空会话失败')
  }
  
  return response.json()
}

/**
 * 重命名会话
 */
export async function renameSession(sessionId, title) {
  const response = await request(`/chat/sessions/${sessionId}/rename`, {
    method: 'PUT',
    body: JSON.stringify({ title })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '重命名会话失败')
  }
  
  return response.json()
}

/**
 * 上传文件
 */
export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  
  const token = getToken()
  const response = await fetch(`${API_BASE_URL}/chat/upload`, {
    method: 'POST',
    headers: {
      ...(token && { 'Authorization': `Bearer ${token}` })
    },
    body: formData
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '文件上传失败')
  }
  
  return response.json()
}

/**
 * 获取可用模型列表（供下拉选择）
 */
export async function getModelList() {
  const response = await request('/models-config/llm-models/selection')
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '获取模型列表失败')
  }
  
  return response.json()
}

/**
 * 删除会话中的消息（同时删除对应的回复/提问）
 * @param {string} sessionId - 会话ID
 * @param {string} messageId - 要删除的消息ID
 */
export async function deleteMessage(sessionId, messageId) {
  const response = await request(`/chat/sessions/${sessionId}/messages/${messageId}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '删除消息失败')
  }

  return response.json()
}

/**
 * 发送聊天消息（SSE流式）
 * @param {string} sessionId
 * @param {string} message
 * @param {AbortSignal} [signal] - 可选 AbortController signal，用于取消请求
 * @param {string} [modelId] - 可选，指定使用的模型ID
 */
export function sendChatMessage(sessionId, message, signal, modelId) {
  const token = getToken()
  
  const body = {
    session_id: sessionId,
    message: message,
    stream: true
  }
  
  // 如果指定了 modelId，则添加到请求体
  if (modelId) {
    body.model_id = modelId
  }
  
  return fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(body),
    signal
  })
}
