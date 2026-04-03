/**
 * 认证模块 API 服务
 * 处理所有与认证相关的 API 请求
 */

import { API_CONFIG } from '../../utils/config.js'

const API_BASE_URL = API_CONFIG.API_BASE_URL

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
    throw new Error(error.detail || '登录失败')
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
    throw new Error(error.detail || '获取用户信息失败')
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
