import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { configLoaderPlugin } from './vite-plugins/config-loader.js'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    configLoaderPlugin(),  // 首先加载配置
    vue()
  ],
})
