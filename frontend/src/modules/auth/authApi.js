/**
 * 认证模块 API 服务
 * 处理所有与认证相关的 API 请求
 */

import { API_CONFIG } from '../../utils/config.js'

const API_BASE_URL = API_CONFIG.API_BASE_URL

/**
 * 从 FastAPI 错误响应中提取可读的错误信息（中文）
 * 兼容两种格式：
 *   - HTTPException → detail 是字符串
 *   - Pydantic 校验失败 (422) → detail 是数组
 */

function extractErrorMessage(errorData) {
  if (!errorData) return '请求失败'
  const detail = errorData.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map(err => {
      const field = err.loc?.slice(-1)[0] || ''
      return translatePydanticError(err.type, field, err.ctx, err.msg)
    }).filter(Boolean).join('；')
  }
  return String(detail || '请求失败')
}

function translatePydanticError(type, field, ctx, rawMsg) {
  const label = FIELD_LABELS[field] || field
  switch (type) {
    // 缺失字段
    case 'missing':
      return `请填写${label}`
    // 字符串长度不足
    case 'string_too_short':
      return `${label}不能少于${ctx?.min_length || ''}位`
    // 字符串过长
    case 'string_too_long':
      return `${label}不能超过${ctx?.max_length || ''}位`
    // 类型或格式错误
    case 'value_error':
    case 'string_type':
    case 'type_error':
      return `${label}格式不正确`
    // 默认兜底
    default:
      return rawMsg || `${label}校验不通过`
  }
}

const FIELD_LABELS = {
  password: '密码长度',
  username: '用户名',
  email: '邮箱',
  full_name: '全名',
  captcha_id: '验证码ID',
  captcha_text: '验证码',
}

/**
 * 用户登录
 */
export async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(extractErrorMessage(error))
  }

  const data = await response.json()

  // 保存登录信息
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('username', data.username)
  localStorage.setItem('role', data.role)

  return data
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser() {
  const token = localStorage.getItem('token')
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(extractErrorMessage(error))
  }

  return response.json()
}

/**
 * 退出登录
 */
export async function logout() {
  const token = localStorage.getItem('token')
  
  try {
    await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
  } catch (e) {
    // 忽略错误
  }

  // 清除本地存储
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
}

/**
 * 用户注册
 */
export async function register(username, password, email, full_name, captcha_id, captcha_text) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password, email, full_name, captcha_id, captcha_text })
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(extractErrorMessage(error))
  }

  return response.json()
}

/**
 * 获取验证码
 */
export async function getCaptcha() {
  const response = await fetch(`${API_BASE_URL}/auth/captcha`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(extractErrorMessage(error))
  }

  return response.json()
}

/**
 * 检查是否已登录
 */
export function isLoggedIn() {
  return !!localStorage.getItem('token')
}

/**
 * 获取token
 */
export function getToken() {
  return localStorage.getItem('token')
}

/**
 * 获取用户名
 */
export function getUsername() {
  return localStorage.getItem('username')
}

/**
 * 获取用户角色
 */
export function getUserRole() {
  return localStorage.getItem('role') || 'user'
}

/**
 * 检查是否是管理员
 */
export function isAdmin() {
  const role = getUserRole()
  return ['admin', 'super_admin'].includes(role)
}

/**
 * 检查是否是超级管理员
 */
export function isSuperAdmin() {
  return getUserRole() === 'super_admin'
}

/**
 * 清除登录状态
 */
export function clearAuth() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
}
