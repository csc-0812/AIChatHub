/**
 * Vite插件：从config.yaml读取配置并生成config.json
 */

import fs from 'fs'
import path from 'path'
import yaml from 'js-yaml'

export function configLoaderPlugin() {
  return {
    name: 'config-loader',
    
    // 在服务器启动时执行
    configureServer(server) {
      generateConfig()
    },
    
    // 在构建时执行
    buildStart() {
      generateConfig()
    }
  }
}

/**
 * 生成配置文件
 */
function generateConfig() {
  try {
    // 读取项目根目录的config.yaml
    const configPath = path.resolve('..', 'config', 'config.yaml')
    
    if (!fs.existsSync(configPath)) {
      console.warn('config.yaml not found, using default config')
      writeDefaultConfig()
      return
    }
    
    // 解析YAML
    const yamlContent = fs.readFileSync(configPath, 'utf8')
    const config = yaml.load(yamlContent)
    
    // 提取前端配置
    const frontendConfig = {
      api_base_url: config.frontend?.api_base_url || 'http://localhost:8000/api/v1',
      app_name: config.app?.name || 'AI Chat'
    }
    
    // 写入public/config.json
    const publicDir = path.resolve('public')
    if (!fs.existsSync(publicDir)) {
      fs.mkdirSync(publicDir, { recursive: true })
    }
    
    const configJsonPath = path.join(publicDir, 'config.json')
    fs.writeFileSync(configJsonPath, JSON.stringify(frontendConfig, null, 2))
    
    console.log('✓ Config generated from config.yaml')
  } catch (error) {
    console.error('Failed to load config.yaml:', error.message)
    writeDefaultConfig()
  }
}

/**
 * 写入默认配置
 */
function writeDefaultConfig() {
  const defaultConfig = {
    api_base_url: 'http://localhost:8000/api/v1',
    app_name: 'AI Chat'
  }
  
  const publicDir = path.resolve('public')
  if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true })
  }
  
  const configJsonPath = path.join(publicDir, 'config.json')
  fs.writeFileSync(configJsonPath, JSON.stringify(defaultConfig, null, 2))
  
  console.log('✓ Default config generated')
}
