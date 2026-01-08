<template>
  <PageShell tab="home">
    <div class="top-bg">
      <div class="greet">
        <!-- 💡 1. 绑定真实昵称 -->
        <div class="hello">你好，{{ userName }}</div>
        <div class="sub">家庭健康助手</div>
      </div>

      <div class="avatars-wrapper">
        <div class="avatars">
          <div v-for="m in members" :key="m.id" class="avatar-item" :class="{ active: m.id === activeMemberId }"
            @click="activeMemberId = m.id">
            <div class="avatar-circle">
              <img v-if="m.avatar_url" :src="m.avatar_url" class="real-avatar" />
              <span v-else class="avatar-icon">👤</span>
            </div>
            <div class="avatar-name">{{ m.name }}</div>
          </div>
        </div>
        <div class="ai-status-bar">
          <span class="ai-sparkle">✨</span>
          <span class="ai-msg">{{ aiGreeting }}</span>
        </div>
      </div>
    </div>

    <div class="content">
      <div class="cards-row">
        <!-- 个性化建议 -->
        <div class="card">
          <div class="card-title">个性化建议</div>

          <!-- 💡 2. 循环显示真实的精简建议 -->
          <template v-if="adviceList.length > 0">
            <div v-for="adv in adviceList" :key="adv.id" class="mini">
              <div class="mini-text">{{ adv.title }}</div>
            </div>
          </template>
          <div v-else class="mini">
            <div class="mini-text light">暂无建议，点击下方开始问诊</div>
          </div>

          <button class="btn pill" @click="router.push('/advice')">
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
            <!-- 💡 修改 1：循环里直接拿 h 即可，Key 建议用真实的 id -->
            <div v-for="h in consultHistory" :key="h.id" class="history-item">
              <!-- 💡 修改 2：重点！这里必须写 h.title -->
              <span style="color: #000;">{{ h.title }}</span>
            </div>

            <!-- 兜底 -->
            <div v-if="consultHistory.length === 0" class="history-item" style="color:#ccc">
              暂无历史记录
            </div>
          </div>

          <!-- 💡 3. 点击跳转到问诊页 -->
          <button class="btn primary" @click="router.push('/consult')">
            开始问诊
          </button>
        </div>
      </div>

      <!-- 健康百科 (保持原样，后期可对接接口) -->
      <div class="wiki">
        <div class="wiki-head">
          <div class="wiki-title">健康百科</div>
          <button class="arrow" @click="router.push('/wiki')">→</button>
        </div>
        <div class="wiki-grid">
          <div v-for="w in wikiCards" :key="w.title" class="wiki-card">
            <div class="wiki-card-title">{{ w.title }}</div>
          </div>
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, onMounted, watch, computed } from "vue";
import { useRouter } from "vue-router";
import { apiGet } from "../api/http";
import PageShell from "../components/PageShell.vue";

const router = useRouter();
const LS_MEMBER_KEY = "active_member_id";

// 1. 变量定义
const userName = ref("加载中...");
const members = ref([]);
const activeMemberId = ref(null);
const adviceList = ref([]); // 首页展示的精简列表
const consultHistory = ref([]); // 存放真实的问诊历史

// 百科静态占位数据
const wikiCards = [
  { title: "高血压防治" },
  { title: "儿童饮食指南" },
  { title: "糖尿病知识" }
];

// 2. 初始化：获取用户信息和成员列表
onMounted(async () => {
  try {
    // A. 获取我的昵称 (从 me 接口拿)
    const user = await apiGet("/me");
    userName.value = user.nickname || "新用户";

    // B. 获取成员列表
    const res = await apiGet("/members");
    members.value = res;

    // 🆕 获取问诊历史
    const sessions = await apiGet("/consult/sessions");
    // 首页只展示最近的 2 个
    consultHistory.value = sessions.slice(0, 3);

    // C. 同步选中状态
    const savedId = localStorage.getItem(LS_MEMBER_KEY);
    if (savedId && res.find(m => m.id == savedId)) {
      activeMemberId.value = parseInt(savedId);
    } else if (res.length > 0) {
      activeMemberId.value = res[0].id;
    }



    // D. 初始加载建议预览
    if (activeMemberId.value) {
      loadPreviewData(activeMemberId.value);
    }

  } catch (e) {
    console.error("首页数据加载失败", e);
    userName.value = "请先登录";
  }
});

// 3. 核心：监听成员切换
watch(activeMemberId, (newId) => {
  if (newId) {
    localStorage.setItem(LS_MEMBER_KEY, newId); // 全局同步钥匙
    loadPreviewData(newId); // 重新加载下方的建议
  }
});

const aiGreeting = computed(() => {
  const m = members.value.find(x => x.id === activeMemberId.value);
  if (!m) return "正在同步家庭健康数据...";

  // 1. 优先逻辑：检查资料完整度
  if (!m.height || !m.weight) {
    return `你好 ${m.name}，建议前往“我的”页面补全身高体重，以便我计算你的健康指标。`;
  }

  // 2. 次要逻辑：根据慢病标签（这里需要你之前改好的字典格式）
  if (m.tags && Object.keys(m.tags).length > 0) {
    const mainTag = Object.keys(m.tags)[0]; // 拿第一个病
    return `今日关注：针对你的${mainTag}情况，我已更新了专科建议，记得查看。`;
  }

  // 3. 兜底逻辑：根据 BMI
  const h = m.height / 100;
  const bmi = (m.weight / (h * h)).toFixed(1);
  if (bmi > 24) return `当前 BMI 为 ${bmi}（偏重），建议今日增加 30 分钟有氧运动。`;

  return `你好 ${m.name}，今天感觉怎么样？我随时待命为您解答健康疑问。`;
});

// 4. 获取该成员的精简版建议 (只取最新两条)
async function loadPreviewData(memberId) {
  try {
    const res = await apiGet(`/advice?member_id=${memberId}`);
    // 首页卡片小，我们只展示最新的 2 条建议
    adviceList.value = res.slice(0, 3);
  } catch (e) {
    adviceList.value = [];
  }
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
  overflow-x: auto;
  /* 👈 开启横向滚动 */
  white-space: nowrap;
  /* 👈 强制不换行 */
  -webkit-overflow-scrolling: touch;
  /* 让手机滑动更丝滑 */
  padding: 10px 0;
}

/* 隐藏丑陋的滚动条 */
.avatars-wrapper::-webkit-scrollbar {
  display: none;
}

.ai-status-bar {
  padding: 8px 24px;
  /* 上下4px，左边空出24px（跟头像对齐或略微缩进） */
  margin-top: 12px;
  /* 紧贴头像栏下方 */
  margin-bottom: 4px;
  margin-right: 12px;
  margin-left: -16px;
}

/* 文字样式：灰色、小号、多行左对齐 */
.ai-msg {
  font-size: 12px;
  /* 字号调小 */
  color: #8a9999;
  /* 阴影感的深灰色 */
  line-height: 1.6;
  /* 增加行高，多行时不拥挤 */
  text-align: left;
  /* 左对齐 */
  white-space: pre-wrap;
  /* 支持逻辑中的换行符 */
  font-weight: 400;
  /* 不要太粗，显得轻盈 */

  /* 增加一个非常淡的文字阴影，增加质感（可选） */
  text-shadow: 0 1px 1px rgba(255, 255, 255, 0.8);
}

/* 2. 内层轨道：负责让成员排成一排 */
.avatars {
  display: inline-flex;
  /* 👈 让内容按行排列 */
  gap: 20px;
  /* 成员之间的间距 */
  padding: 0 16px;
  /* 给左右两边留点空，防止贴边 */
}

/* 3. 每个成员的样式 */
.avatar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  /* 👈 关键：防止宽度被挤压变扁 */
  cursor: pointer;
  transition: all 0.3s ease;
}

.avatar-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #f0f4f4;
  border: 2px solid transparent;
  /* 默认透明边框 */
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
  border-color: #17a2a2;
  /* 选中时边框变色 */
  background: #e0f2f2;
  transform: translateY(-5px);
  /* 选中时往上弹一点点，更灵动 */
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
