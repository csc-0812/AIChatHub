/**
 * 主题管理工具
 * 支持写入 data-theme 属性到 <html> 元素，持久化到 localStorage
 */

const THEME_KEY = 'app-theme'
const DEFAULT_THEME = 'dark-cobalt'

export const THEMES = {
  'dark-cobalt': { label: '深色·钴蓝', icon: '🌙' },
  'light': { label: '浅色', icon: '☀️' },
  'amber-dark': { label: '深色·琥珀', icon: '🌅' }
}

export function getSavedTheme() {
  return localStorage.getItem(THEME_KEY) || DEFAULT_THEME
}

export function setTheme(name) {
  const valid = Object.keys(THEMES).includes(name) ? name : DEFAULT_THEME
  localStorage.setItem(THEME_KEY, valid)
  document.documentElement.setAttribute('data-theme', valid)
  return valid
}

export function getThemeInfo(name) {
  return THEMES[name] || THEMES[DEFAULT_THEME]
}

export function initTheme() {
  setTheme(getSavedTheme())
}
