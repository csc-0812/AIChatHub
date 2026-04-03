/**
 * 前端配置文件
 * 从 public/config.json 读取配置
 */

// 默认配置（用于初始化和fallback）
const DEFAULT_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  API_PREFIX: '/api/v1',
  APP_NAME: 'AI Chat'
}

// 当前配置
let currentConfig = { ...DEFAULT_CONFIG }

// 配置加载状态
let isLoaded = false

/**
 * 从 public/config.json 加载配置
 */
export async function loadConfig() {
  // 如果已经加载过，直接返回
  if (isLoaded) {
    return currentConfig
  }

  try {
    // 从 public/config.json 读取配置
    const response = await fetch('/config.json')
    if (response.ok) {
      const data = await response.json()
      
      // 解析api_base_url
      if (data.api_base_url) {
        const urlObj = new URL(data.api_base_url)
        currentConfig.BASE_URL = `${urlObj.protocol}//${urlObj.host}`
        currentConfig.API_PREFIX = urlObj.pathname
      }
      
      if (data.app_name) {
        currentConfig.APP_NAME = data.app_name
      }
      
      isLoaded = true
      console.log('配置已加载:', currentConfig)
    }
  } catch (error) {
    console.warn('从config.json加载配置失败，使用默认配置:', error)
    // 使用默认配置
    currentConfig = { ...DEFAULT_CONFIG }
  }
  
  return currentConfig
}

/**
 * 获取API配置
 */
export const API_CONFIG = {
  get BASE_URL() {
    return currentConfig.BASE_URL
  },
  get API_PREFIX() {
    return currentConfig.API_PREFIX
  },
  get API_BASE_URL() {
    return currentConfig.BASE_URL + currentConfig.API_PREFIX
  }
}

/**
 * 获取应用配置
 */
export const APP_CONFIG = {
  get APP_NAME() {
    return currentConfig.APP_NAME
  },
  DEFAULT_PAGE_SIZE: 20,
  MAX_MESSAGE_LENGTH: 4000
}

/**
 * 更新配置（用于动态修改）
 * @param {Object} newConfig 
 */
export function updateConfig(newConfig) {
  currentConfig = { ...currentConfig, ...newConfig }
}

/**
 * 重置为默认配置
 */
export function resetConfig() {
  currentConfig = { ...DEFAULT_CONFIG }
  isLoaded = false
}

// 导出默认配置对象
export default {
  API: API_CONFIG,
  APP: APP_CONFIG,
  load: loadConfig,
  update: updateConfig,
  reset: resetConfig
}
