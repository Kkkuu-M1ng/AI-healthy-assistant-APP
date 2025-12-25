<template>
  <PageShell tab="home">
    <!-- 顶部渐变背景 -->
    <div class="top-bg">
      <div class="greet">
        <div class="hello">你好，{{ userName }}</div>
        <div class="sub">家庭健康助手</div>
      </div>

      <!-- 家庭头像区 -->
      <div class="avatars">
        <div
          v-for="m in members"
          :key="m.id"
          class="avatar-item"
          :class="{ active: m.id === activeMemberId }"
          @click="activeMemberId = m.id"
        >
          <div class="avatar-circle">
            <span class="avatar-icon">👤</span>
          </div>
          <div class="avatar-name">{{ m.name }}</div>
        </div>
      </div>
    </div>

    <!-- 中间内容区 -->
    <div class="content">
      <div class="cards-row">
        <!-- 个性化建议 -->
        <div class="card">
          <div class="card-title">个性化建议</div>

          <div class="mini">
            <div class="mini-text">{{ suggestionTitle }}</div>
          </div>

          <div class="mini input-like">
            <div class="mini-text light">{{ suggestionDetail }}</div>
          </div>

          <!-- 这里后面我们会改成跳转 /advice -->
          <button class="btn pill" @click="toast('查看更多建议')">
            查看更多建议
          </button>
        </div>

        <!-- AI 智能问诊 -->
        <div class="card">
          <div class="card-head">
            <div class="card-title">AI智能问诊</div>
            <div class="robot">🤖</div>
          </div>

          <div class="hint">描述您的症状，我来帮您分析</div>

          <div class="history">
            <div
              v-for="(h, idx) in consultHistory"
              :key="idx"
              class="history-item"
              @click="toast('打开：' + h)"
            >
              {{ h }}
            </div>
          </div>

          <!-- 这里后面我们会改成跳转 /consult -->
          <button class="btn primary" @click="toast('开始问诊')">
            开始问诊
          </button>
        </div>
      </div>

      <!-- 健康百科 -->
      <div class="wiki">
        <div class="wiki-head">
          <div class="wiki-title">健康百科</div>

          <!-- 这里后面我们会改成跳转 /wiki -->
          <button class="arrow" @click="toast('进入健康百科列表')">→</button>
        </div>

        <div class="wiki-grid">
          <div
            v-for="w in wikiCards"
            :key="w.title"
            class="wiki-card"
            @click="toast('打开：' + w.title)"
          >
            <div class="wiki-card-title">{{ w.title }}</div>
          </div>
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref } from "vue";
import PageShell from "../components/PageShell.vue";

const userName = ref("XXX");

const members = ref([
  { id: 1, name: "我" },
  { id: 2, name: "爸爸" },
  { id: 3, name: "儿子" },
]);

const activeMemberId = ref(1);

const suggestionTitle = ref("孩子体重偏…多跑步");
const suggestionDetail = ref("孩子……");

const consultHistory = ref(["历史记录1", "历史记录2", "历史记录3", "历史记录4"]);

const wikiCards = ref([
  { title: "高血压防治" },
  { title: "儿童饮食指南" },
  { title: "糖尿病知识" },
]);

function toast(msg) {
  alert(msg);
}
</script>

<style scoped>

/* 顶部背景 */
.top-bg {
  background: linear-gradient(180deg, #d7f3f4 0%, #f7fbfb 70%);
  width: 100%;
  padding: 10px 16px 12px;
}

/* 状态栏 */
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #2f3a3a;
  font-size: 12px;
  margin-bottom: 6px;
}

/* 问候语 */
.greet {
  margin: 6px 0 10px;
  text-align: left;
}
.hello {
  font-size: 16px;
  font-weight: 700;
  color: #1f2b2b;
}
.sub {
  margin-top: 2px;
  font-size: 13px;
  color: #3f5b5b;
}

/* 头像栏 */
.avatars {
  display: flex;
  justify-content: center;  
  align-items: center;       
  gap: 18px;                
  padding: 8px 0 2px;
}
.avatar-item {
  display: grid;
  justify-items: center;
  gap: 6px;
  cursor: pointer;
}
.avatar-circle {
  width: 58px;
  height: 58px;
  border-radius: 999px;
  background: #0f0f0f;
  display: grid;
  place-items: center;
  box-shadow: 0 2px 0 rgba(0, 0, 0, 0.06);
}
.avatar-icon {
  filter: grayscale(1) brightness(2);
  font-size: 18px;
}
.avatar-name {
  font-size: 12px;
  color: #1f2b2b;
}
.avatar-item.active .avatar-circle {
  outline: 3px solid rgba(64, 158, 255, 0.35);
}

/* 内容区 */
.content {
  padding: 10px 12px 0;
}

/* 两张卡片一行 */
.cards-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

/* 卡片样式 */
.card {
  background: #ffffff;
  border: 1px solid #dfeeee;
  border-radius: 10px;
  padding: 10px;
  box-sizing: border-box;
  min-height: 210px;
}
.card-title {
  font-size: 14px;
  font-weight: 800;
  color: #1f2b2b;
  margin-bottom: 8px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.robot {
  font-size: 18px;
}

.mini {
  border: 1px solid #e6f2f2;
  background: #f3fbfb;
  border-radius: 6px;
  padding: 8px;
  margin-bottom: 8px;
}
.input-like {
  background: #ffffff;
}
.mini-text {
  font-size: 12px;
  color: #1f2b2b;
}
.mini-text.light {
  color: #567;
}

/* AI 提示+历史记录 */
.hint {
  font-size: 12px;
  color: #567;
  margin: 6px 0 8px;
}
.history {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
}
.history-item {
  border: 1px solid #e7efef;
  background: #ffffff;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 12px;
  cursor: pointer;
}

/* 按钮 */
.btn {
  width: 100%;
  border: none;
  cursor: pointer;
  padding: 10px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
}
.btn.pill {
  background: #a9d6ef;
  color: #ffffff;
}
.btn.primary {
  background: #2e7bdc;
  color: #fff;
}
.btn:hover {
  opacity: 0.92;
}

/* 健康百科 */
.wiki {
  margin-top: 10px;
  background: #ffffff;
  border: 1px solid #dfeeee;
  border-radius: 10px;
  padding: 10px;
}
.wiki-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.wiki-title {
  font-size: 14px;
  font-weight: 800;
  color: #1f2b2b;
}
.arrow {
  border: none;
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}
.wiki-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 8px;
}
.wiki-card {
  height: 78px;
  border: 1px solid #e7efef;
  background: #ffffff;
  border-radius: 8px;
  padding: 8px;
  cursor: pointer;
  box-sizing: border-box;
}
.wiki-card-title {
  font-size: 12px;
  font-weight: 700;
  color: #1f2b2b;
}

</style>
