import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/xiao-zhi-ai/',    // 关键！前端资源基础路径改成这个子路径
  server: {
    host: true,
    port: 5173,
    proxy: {
      // 这里代理时，前端开发时请求的api路径应该带 /xiao-zhi-ai/api 开头
      '/xiao-zhi-ai/api': {
        target: 'http://backend_xiao_zhi_ai:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/xiao-zhi-ai\/api/, '/api'), 
      },
    },
  },
});
