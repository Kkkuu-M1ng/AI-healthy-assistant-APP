<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue';

onMounted(() => {
  // 1. 获取当前完整的 URL
  const currentUrl = window.location.href;
  console.log("📍 收到微信回调网址:", currentUrl);

  // 2. 强行在 URL 里搜索 'token=' 字符
  if (currentUrl.includes('token=')) {
    try {
      // 💡 简单的切割法，把 Token 拿出来
      const token = currentUrl.split('token=')[1];
      
      if (token) {
        // 3. 存入你的 Token 盒子 (ai_token)
        localStorage.setItem("ai_token", token);
        console.log("✅ 微信 Token 捡起成功!");

        // 4. 【高光动作】强行重定向到干净的首页，刷掉 404 状态
        // 这一步会瞬间把地址栏变回干净的 /#/home
        window.location.href = window.location.origin + window.location.pathname + "#/home";
      }
    } catch (e) {
      console.error("解析 Token 失败", e);
    }
  }
});
</script>