/**
 * 管理员模块 API 服务
 * 处理所有与管理后台相关的 API 请求
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
 * 获取系统状态
 */
export async function getSystemStatus() {
  const response = await request('/admin/system/status')

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '获取系统状态失败')
  }

  return response.json()
}

/**
 * 获取用户列表
 */
export async function getUsers() {
  const response = await request('/admin/users')

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '获取用户列表失败')
  }

  return response.json()
}

/**
 * 创建用户
 */
export async function createUser(userData) {
  const response = await request('/admin/users', {
    method: 'POST',
    body: JSON.stringify(userData)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '创建用户失败')
  }

  return response.json()
}

/**
 * 更新用户
 */
export async function updateUser(username, userData) {
  const response = await request(`/admin/users/${username}`, {
    method: 'PUT',
    body: JSON.stringify(userData)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '更新用户失败')
  }

  return response.json()
}

/**
 * 删除用户
 */
export async function deleteUser(username) {
  const response = await request(`/admin/users/${username}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '删除用户失败')
  }

  return response.json()
}

/**
 * 切换用户启用/禁用状态
 */
export async function toggleUser(username) {
  const response = await request(`/admin/users/${username}/toggle`, {
    method: 'POST'
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '操作失败')
  }

  return response.json()
}

/**
 * 重置用户密码
 */
export async function resetPassword(username, newPassword) {
  const response = await request(`/admin/users/${username}/reset-password`, {
    method: 'POST',
    body: JSON.stringify({ new_password: newPassword })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '重置密码失败')
  }

  return response.json()
}

/**
 * 修改用户角色
 */
export async function updateUserRole(username, role) {
  const response = await request(`/admin/users/${username}/role`, {
    method: 'PUT',
    body: JSON.stringify({ role })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '修改角色失败')
  }

  return response.json()
}

/**
 * 获取模型配置列表
 */
export async function getLLMModels() {
  const response = await request('/models-config/llm-models')

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '获取模型配置失败')
  }

  return response.json()
}

/**
 * 创建模型配置
 */
export async function createLLMModel(modelData) {
  const response = await request('/models-config/llm-models', {
    method: 'POST',
    body: JSON.stringify(modelData)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '创建模型配置失败')
  }

  return response.json()
}

/**
 * 更新模型配置
 */
export async function updateLLMModel(modelId, modelData) {
  const response = await request(`/models-config/llm-models/${modelId}`, {
    method: 'PUT',
    body: JSON.stringify(modelData)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '更新模型配置失败')
  }

  return response.json()
}

/**
 * 删除模型配置
 */
export async function deleteLLMModel(modelId) {
  const response = await request(`/models-config/llm-models/${modelId}`, {
    method: 'DELETE'
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '删除模型配置失败')
  }

  return response.json()
}

/**
 * 启用模型
 */
export async function activateLLMModel(modelId) {
  const response = await request(`/models-config/llm-models/${modelId}/activate`, {
    method: 'POST'
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || '启用模型失败')
  }

  return response.json()
}
