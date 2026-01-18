import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  
  // 👇👇👇 重点修改这里 👇👇👇
  server: {
    // 允许所有主机访问，这样 cpolar 随机生成的域名也能进来了
    allowedHosts: true,
    
    // 💡 额外赠送一个小配置：
    // 让你电脑在局域网内也能被访问（比如你在同一个 WiFi 下的手机）
    host: '0.0.0.0' 
  }
})