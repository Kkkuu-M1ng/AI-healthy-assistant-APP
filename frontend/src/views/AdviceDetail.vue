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

        <div class="section">
          <div class="st">为什么给你这个建议？</div>
          <div class="p">{{ advice.reason }}</div>
        </div>

        <div class="section">
          <div class="st">💡 怎么做 (Actions)</div>
          <ul class="ul">
            <li v-for="(action, i) in advice.actions" :key="i">
              {{ action.text }}
            </li>
          </ul>
        </div>

        <div class="section">
          <div class="st">📌 注意事项 (Tips)</div>
          <ul class="ul tips-ul">
            <li v-for="(tip, i) in advice.tips" :key="i">
              {{ tip }}
            </li>
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
const advice = ref({
  title: "加载中...",
  reason: "",
  actions: [], // 👈 新增
  tips: []     // 👈 新增
});
const loading = ref(true);

// 2. 页面加载时抓取真实数据
async function fetchDetail() {
  loading.value = true;
  try {
    const res = await apiGet(`/advice/${id.value}`);

    // 1. 核心修复：手动解析 detail_json
    let detailData = { actions: [], tips: [] };
    if (res.detail_json) {
      try {
        const parsed = JSON.parse(res.detail_json);
        detailData.actions = parsed.actions || [];
        detailData.tips = parsed.tips || [];
      } catch (e) {
        console.error("解析 detail_json 失败");
      }
    }

    // 2. 赋值
    advice.value = {
      ...res,
      actions: detailData.actions,
      tips: detailData.tips
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
.page {
  box-sizing: border-box;
  width: 100%;
  max-width: 450px;
  /* 👈 建议设为 450px，这是最美观的手机预览宽度 */

  margin: 0 auto;
  /* 👈 居中 */
  padding: 16px;
}

.nav {
  display: grid;
  grid-template-columns: 36px 1fr 36px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.back {
  width: 36px;
  height: 36px;
  border: 2px solid #e7efef;
  background: #fff;
  border-radius: 12px;
  font-size: 22px;
  cursor: pointer;
  display: flex;
  /* 变成 flex 容器 */
  justify-content: center;
  /* 水平居中 */
  align-items: center;
  /* 垂直居中 */
}

.title {
  text-align: center;
  font-weight: 900;
  color: #123;
}

.spacer {
  width: 36px;
  height: 36px;
}

.card {
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 12px;
}

.h1 {
  font-size: 24px;
  font-weight: 900;
  color: #123;
}

.sub {
  margin-top: 6px;
  font-size: 12px;
  color: #6b7f7f;
}

.section {
  margin-top: 12px;
}

.st {
  font-weight: 900;
  color: #123;
  margin-bottom: 6px;
  text-align: left;
  font-size: 22px;
  margin-top: 30px;

}

.p {
  font-size: 14px;
  color: #2a3c3c;
  line-height: 1.6;
  text-align: left;
}

.ul {
  margin: 0;
  padding-left: 18px;
  font-size: 16px;
  color: #2a3c3c;
  line-height: 1.6;
  text-align: left;
}

.warn {
  margin-top: 12px;
  font-size: 12px;
  color: #6b7f7f;
}
</style>
