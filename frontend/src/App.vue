<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue';
import { useRouter } from 'vue-router'; // 👈 确保导入了 useRouter

const router = useRouter(); // 👈 确保初始化了

onMounted(() => {
  const currentUrl = window.location.href;
  console.log("📍 页面加载，收到的完整 URL:", currentUrl); // 👈 看这里打印了啥

  const tokenParts = currentUrl.split('token=');
  if (tokenParts.length > 1) {
    const token = tokenParts[1];
    if (token) {
      localStorage.setItem("ai_token", token);
      console.log("✅ Token 已存入: ", token);
      router.replace({ path: '/home' }); // 清理 URL
    }
  }
});
</script>