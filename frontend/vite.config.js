import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// /api 请求的代理目标（后端地址）：
//   本地开发：不设置该变量，默认代理到本机启动的后端 http://localhost:8080（行为与之前完全一致）
//   Docker 环境：由 docker-compose 注入 VITE_API_TARGET=http://backend:8080
//     （容器内的 localhost 指向容器自身，只能用 compose 的服务名 backend 才能连到后端容器）
const apiTarget = process.env.VITE_API_TARGET || 'http://localhost:8080'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true
      }
    }
  }
})
