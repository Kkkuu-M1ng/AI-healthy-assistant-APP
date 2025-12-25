<template>
  <div class="app">
    <slot />
    <div class="content">
      
    </div>

    <div class="tabbar">
      <div class="tab" :class="{ on: tab === 'home' }" @click="go('/home')">
        <div class="ico">🏠</div><div class="txt">首页</div>
      </div>
      <div class="tab" :class="{ on: tab === 'advice' }" @click="go('/advice')">
        <div class="ico">✨</div><div class="txt">建议</div>
      </div>
      <div class="tab" :class="{ on: tab === 'consult' }" @click="go('/consult')">
        <div class="ico">💬</div><div class="txt">问诊</div>
      </div>
      <div class="tab" :class="{ on: tab === 'me' }" @click="go('/me')">
        <div class="ico">👤</div><div class="txt">我的</div>
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
.app{
  width: 393px;
  height: 852px;

  background: #f7fbfb;

  position: relative;
  overflow: hidden;          /* 防止内容溢出 */

  box-sizing: border-box;
}

.top{padding:12px 16px 8px}
.title{font-size:16px;font-weight:800;color:#1f2b2b}
.content{
  padding: 0 16px;          /* 左右挤压 */
  box-sizing: border-box;
}


.tabbar{
  position:absolute;left:0;right:0;bottom:0;height:64px;
  background:#fff;border-top:1px solid #e7efef;
  display:grid;grid-template-columns:repeat(4,1fr);
  padding:6px 6px 8px;box-sizing:border-box;
}
.tab{display:grid;justify-items:center;align-content:center;gap:2px;color:#7a8b8b;cursor:pointer}
.tab.on{color:#17a2a2;font-weight:800}
.ico{font-size:18px}
.txt{font-size:11px}
</style>
