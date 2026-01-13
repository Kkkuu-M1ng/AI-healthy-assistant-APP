<template>
  <PageShell tab="advice">
    <div class="page">
      <!-- 顶部栏保持不变 -->
      <div class="nav">
        <button class="back" @click="router.back()">‹</button>
        <div class="title">建议详情</div>
        <div class="spacer"></div>
      </div>

      <!-- 👇👇👇 重点修复：加上 v-if="advice" 👇👇👇 -->
      <div v-if="advice" class="card">
        <div class="h1">{{ advice.title }}</div>
        <div class="sub">ID：{{ id }}</div>

        <div class="section">
          <div class="st">为什么给你这个建议</div>
          <div class="p">{{ advice.reason }}</div>
        </div>

        <div class="section">
          <div class="st">怎么做</div>
          <ul class="ul">
            <!-- 💡 这里的变量名要和你脚本里 map 出来的名字对应 -->
            <li v-for="(x, i) in advice.steps" :key="i">{{ x }}</li>
          </ul>
        </div>

        <div class="warn">
          ⚠️ 本内容用于健康管理科普，不替代医生诊断；如不适明显请及时就医。
        </div>
      </div>

      <!-- 💡 加一个加载中的提示，体验更好 -->
      <div v-else class="empty">
        正在调取电子病历...
      </div>

      <div style="height: 80px;"></div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import PageShell from "../components/PageShell.vue";
// 💡 引入 apiGet
import { apiGet } from "../api/http";

const route = useRoute();
const router = useRouter();

// 1. 定义变量
const id = computed(() => route.params.id);
const advice = ref(null); // 初始为空
const loading = ref(true);

// 2. 页面加载时抓取真实数据
async function fetchDetail() {
  loading.value = true;
  try {
    // 调用后端：GET /api/advice/{id}
    const res = await apiGet(`/advice/${id.value}`);
    
    // 💡 适配后端字段：
    // 后端存的是 detail_json (字符串)，我们需要解析它
    // 如果没有 detail_json，就给个默认数组
    advice.value = {
      ...res,
      steps: res.detail ? res.detail : ["按照问诊时的医嘱执行", "如有不适请及时停用"]
    };
  } catch (e) {
    console.error("加载建议详情失败", e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchDetail();
});
</script>

<style scoped>
.page{
  padding: 12px 12px 0;
  box-sizing: border-box;
}

.nav{
  display: grid;
  grid-template-columns: 36px 1fr 36px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.back{
  width: 36px; height: 36px;
  border: 1px solid #e7efef;
  background: #fff;
  border-radius: 12px;
  font-size: 22px;
  cursor: pointer;
}
.title{
  text-align: center;
  font-weight: 900;
  color: #123;
}
.spacer{ width: 36px; height: 36px; }

.card{
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 12px;
}
.h1{ font-size: 15px; font-weight: 900; color:#123; }
.sub{ margin-top: 6px; font-size: 12px; color:#6b7f7f; }

.section{ margin-top: 12px; }
.st{ font-weight: 900; color:#123; margin-bottom: 6px; }
.p{ font-size: 13px; color:#2a3c3c; line-height: 1.6; }
.ul{ margin:0; padding-left: 18px; font-size: 13px; color:#2a3c3c; line-height: 1.6; }

.warn{
  margin-top: 12px;
  font-size: 12px;
  color:#6b7f7f;
}
</style>
