<template>
  <div class="app">
    <slot />
    <div class="content">

    </div>

    <div class="tabbar">
      <div class="tab" :class="{ on: tab === 'home' }" @click="go('/home')">
        <div class="ico">🏠</div>
        <div class="txt">首页</div>
      </div>
      <div class="tab" :class="{ on: tab === 'advice' }" @click="go('/advice')">
        <div class="ico">✨</div>
        <div class="txt">建议</div>
      </div>
      <div class="tab" :class="{ on: tab === 'consult' }" @click="go('/consult')">
        <div class="ico">💬</div>
        <div class="txt">问诊</div>
      </div>
      <div class="tab" :class="{ on: tab === 'me' }" @click="go('/me')">
        <div class="ico">👤</div>
        <div class="txt">我的</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

defineProps({
  tab: { type: String, default: "home" },
});

const router = useRouter();
function go(path) {
  if (router.currentRoute.value.path !== path) router.push(path);
}
</script>

<style scoped>
.app {
  
  /* ✅ 改为以下代码 */
  width: 100%;         /* 占满屏幕宽度 */
  height: 100vh;        /* 占满屏幕高度 */
  max-width: 100%; 
  padding: 0;
  margin: 0 auto;       /* 在电脑上居中显示 */
  overflow-x: hidden;
  background: linear-gradient(0deg, #f5f9f8 0%, #dff5ef 100%);
  position: relative;
  overflow: hidden;         
  box-sizing: border-box;
}

.title {
  font-size: 16px;
  font-weight: 800;
  color: #1f2b2b
}

.content {
  flex: 1;
  overflow-x: hidden;
  overflow-y: auto; /* 只让中间这块滚 */
  padding: 0; /* 👈 这里必须设为 0 */

  width: 100% !important;
  box-sizing: border-box !important;
  max-width: 100% !important;
  margin-left: 0 !important;
  margin-right: 0 !important;
}

.tabbar {
  position: absolute; bottom: 0; left: 0; right: 0;
  height: 64px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-top: 1px solid rgba(23, 162, 162, 0.1);
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  z-index: 100;
}

.tab {
  display: grid;
  justify-items: center;
  align-content: center;
  gap: 2px;
  color: #7a8b8b;
  cursor: pointer
}

.tab.on {
  color: #17a2a2;
  font-weight: 800
}

.ico {
  font-size: 18px
}

.txt {
  font-size: 11px
}
</style>
