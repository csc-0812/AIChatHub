import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import { loadConfig } from './utils/config.js'

// 先加载配置，再启动应用
async function bootstrap() {
  // 从后端加载配置
  await loadConfig()
  
  // 创建并挂载应用
  createApp(App).mount('#app')
}

bootstrap()
