<template>
  <PageShell tab="advice">
    <div class="page">
      <!-- 顶部栏 -->
      <div class="nav">
        <button class="back" @click="router.back()">‹</button>
        <div class="title">建议详情</div>
        <div class="spacer"></div>
      </div>

      <!-- 内容 -->
      <div class="card">
        <div class="h1">{{ advice.title }}</div>
        <div class="sub">ID：{{ id }}</div>

        <div class="section">
          <div class="st">为什么给你这个建议</div>
          <div class="p">{{ advice.reason }}</div>
        </div>

        <div class="section">
          <div class="st">怎么做</div>
          <ul class="ul">
            <li v-for="(x,i) in advice.steps" :key="i">{{ x }}</li>
          </ul>
        </div>

        <div class="warn">
          ⚠️ 本内容用于健康管理科普，不替代医生诊断；如不适明显请及时就医。
        </div>
      </div>

      <!-- 预留给 tabbar 的安全区 -->
      <div style="height: 80px;"></div>
    </div>
  </PageShell>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import PageShell from "../components/PageShell.vue";

const route = useRoute();
const router = useRouter();

const id = computed(() => route.params.id);

// 先用假数据：后面我们再接入「个性化建议/任务」真实数据
const advice = computed(() => {
  // 你也可以按 id 做不同内容，这里先写一份固定模板
  return {
    title: "控制盐摄入，优先采用低盐饮食",
    reason: "根据你的健康画像（示例），低盐饮食有助于血压与心血管风险管理。",
    steps: [
      "每日食盐建议≤5g，少吃腌制/加工食品。",
      "外卖选择“少盐/不加酱”，汤尽量少喝。",
      "连续 2 周记录变化，再调整策略。"
    ],
  };
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
