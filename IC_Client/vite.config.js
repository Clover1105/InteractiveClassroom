import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  // 设置启动的端口号 -- 默认5173
  server:{
    host:'localhost',
    port:8080,
    open:true // 启动时自动打开浏览器
  }
})
