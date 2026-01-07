<template>
  <PageShell tab="home">
    <!-- 顶部渐变背景 -->
    <div class="top-bg">
      <div class="greet">
        <div class="hello">你好，{{ userName }}</div>
        <div class="sub">家庭健康助手</div>
      </div>

      <!-- 家庭头像区 -->
      <div class="avatars-wrapper"> <!-- 1. 新增：这是限制宽度的窗户 -->
        <div class="avatars"> <!-- 2. 这是会自动延长的轨道 -->
          <div v-for="m in members" :key="m.id" class="avatar-item" :class="{ active: m.id === activeMemberId }"
            @click="activeMemberId = m.id">
            <div class="avatar-circle">
              <!-- 💡 小技巧：如果有头像链接就显示图，没有就显示图标 -->
              <img v-if="m.avatar_url" :src="m.avatar_url" class="real-avatar" />
              <span v-else class="avatar-icon">👤</span>
            </div>
            <div class="avatar-name">{{ m.name }}</div>
          </div>
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
            <div v-for="(h, idx) in consultHistory" :key="idx" class="history-item" @click="toast('打开：' + h)">
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
          <div v-for="w in wikiCards" :key="w.title" class="wiki-card" @click="toast('打开：' + w.title)">
            <div class="wiki-card-title">{{ w.title }}</div>
          </div>
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, onMounted, computed, watch} from "vue";
import { apiGet } from "../api/http";
import PageShell from "../components/PageShell.vue";

const LS_MEMBER_KEY = "active_member_id";

// 1. 定义变量
const members = ref([]); // 存放全家人
const activeMemberId = ref(null); // 当前选中的“副卡ID” (FamilyMember.id)
const adviceList = ref([]); // 存放建议预览

// 2. 页面加载：去后端抓人
onMounted(async () => {
  try {
    // 获取当前用户旗下的所有家庭成员
    const res = await apiGet("/members");
    members.value = res;

    const savedId = localStorage.getItem(LS_MEMBER_KEY);

    if (savedId && res.find(m => m.id == savedId)) {
      activeMemberId.value = parseInt(savedId);
    } else if (res.length > 0) {
      // 没记过或者是脏数据，默认选第一个
      activeMemberId.value = res[0].id;
    }
 
    loadPreviewData(res[0].id);
    
  } catch (e) {
    console.error("首页数据初始化失败");
  }
});

watch(activeMemberId, (newId) => {
  if (newId) {
    // 💡 只要 ID 变了，就立刻记在小本子上
    localStorage.setItem(LS_MEMBER_KEY, newId);
    loadPreviewData(newId);
  }
});

// 3. 点击头像切换人选
function handleSelectMember(id) {
  activeMemberId.value = id;
  loadPreviewData(id); // 切换后，下方的建议也跟着变
}

// 4. 获取该成员的精简版建议（对应你 UI 左侧的卡片）
async function loadPreviewData(memberId) {
  const res = await apiGet(`/advice?member_id=${memberId}`);
  // 只取前两条做精简展示
  adviceList.value = res.slice(0, 2);
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
.avatars-wrapper {
  width: 100%;
  overflow-x: auto;          /* 👈 开启横向滚动 */
  white-space: nowrap;       /* 👈 强制不换行 */
  -webkit-overflow-scrolling: touch; /* 让手机滑动更丝滑 */
  padding: 10px 0;
}

/* 隐藏丑陋的滚动条 */
.avatars-wrapper::-webkit-scrollbar {
  display: none;
}

/* 2. 内层轨道：负责让成员排成一排 */
.avatars {
  display: inline-flex;      /* 👈 让内容按行排列 */
  gap: 20px;                 /* 成员之间的间距 */
  padding: 0 16px;           /* 给左右两边留点空，防止贴边 */
}

/* 3. 每个成员的样式 */
.avatar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;            /* 👈 关键：防止宽度被挤压变扁 */
  cursor: pointer;
  transition: all 0.3s ease;
}

.avatar-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #f0f4f4;
  border: 2px solid transparent; /* 默认透明边框 */
  display: grid;
  place-items: center;
  overflow: hidden;
}

.real-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-item.active .avatar-circle {
  border-color: #17a2a2;      /* 选中时边框变色 */
  background: #e0f2f2;
  transform: translateY(-5px); /* 选中时往上弹一点点，更灵动 */
}

.avatar-item.active .avatar-name {
  color: #17a2a2;
  font-weight: bold;
}

.avatar-name {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
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
  background: #ffffff;
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
  color: 1f2b2b;
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
  background: #2e7bdc;
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
