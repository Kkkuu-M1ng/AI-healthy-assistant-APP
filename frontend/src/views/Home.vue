<template>
  <PageShell tab="home">
    <div class="home-container"> <!-- 💡 确保最外层有这个类名 -->
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
        <div class="dashboard">
          <!-- 1. BMI 仪表盘 -->
          <div class="dash-item bmi-box">
            <div class="dash-label">健康体征 BMI</div>
            <div class="bmi-value" :style="{ color: bmiInfo.color }">{{ bmiInfo.val || '--' }}</div>
            <div class="bmi-bar-bg">
              <div class="bmi-pointer" :style="{ left: bmiInfo.pos + '%', backgroundColor: bmiInfo.color }"></div>
            </div>
            <div class="dash-status">{{ bmiInfo.status }}</div>
          </div>

          <!-- 2. 风险信号灯 (标签) -->
          <div class="dash-item risk-box">
            <div class="dash-label">核心风险</div>
            <div class="risk-tags">
              <div v-for="(val, name) in activeMember?.tags" :key="name" class="risk-dot" :class="'lv-' + val.level">
                {{ name }}
              </div>
              <div v-if="!activeMember?.tags || Object.keys(activeMember.tags).length === 0" class="none-text">暂无风险
              </div>
            </div>
          </div>

          <!-- 3. 任务能量环 -->
          <div class="dash-item task-box">
            <div class="dash-label">任务概览</div>
            <div class="task-circle">
              <span class="task-num">{{ taskStats.done }}/{{ taskStats.total }}</span>
            </div>
            <div class="dash-status">总进度 {{ Math.round((taskStats.done / taskStats.total || 0) * 100) }}%</div>
          </div>
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
              <div class="mini-text" @click="router.push(`/advice/${adv.id}`)">{{ adv.title }} </div>
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
            <div v-for="h in consultHistory" :key="h.id" class="history-item" @click="goHistoryConsult(h)">
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
      <div class="wiki-section">
        <!-- 1. 顶部入口 -->
        <div class="wiki-nav" @click="router.push('/wiki')">
          <div class="wiki-title">健康百科</div>
          <div class="wiki-arrow">查看全部 →</div>
        </div>

        <!-- 2. 下部轮播区 -->
        <div class="wiki-carousel" ref="carouselRef">
          <div v-for="article in wikiList" :key="article.id" class="wiki-slide"
            @click="router.push(`/wiki/${article.id}`)">
            <!-- 背景图 (如果没有存图，我们就用占位色块或网图) -->
            <img :src="'http://127.0.0.1:8000' + article.cover_url" class="slide-img" />

            <!-- 💡 关键：黑色渐变蒙层 -->
            <div class="slide-overlay"></div>

            <!-- 文字内容 -->
            <div class="slide-info">
              <div class="slide-tag">{{ formatCategory(article.category) }}</div>
              <div class="slide-h1">{{ article.title }}</div>
            </div>
          </div>
        </div>
        <div class="dots">
          <div v-for="(art, index) in wikiList" :key="index" class="dot" :class="{ active: currentIndex === index }">
          </div>
        </div>
      </div>
      <div class="safe-bottom"></div>
    </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from "vue";
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
const wikiList = ref([]);

// 1. 任务进度计算
const taskStats = ref({ total: 0, done: 0 });

const carouselRef = ref(null);
const currentIndex = ref(0);
let timer = null;

// 1. 监听滚动，更新小圆点状态
function handleScroll(e) {
  const scrollLeft = e.target.scrollLeft;
  // 💡 这里的 0.88 必须和你 CSS 里的 flex: 0 0 88% 一致
  const itemWidth = e.target.offsetWidth * 0.88; 
  currentIndex.value = Math.round(scrollLeft / itemWidth);
}

// 2. 自动播放逻辑
function startAutoPlay() {
  stopAutoPlay(); // 先清除旧的
  timer = setInterval(() => {
    if (!carouselRef.value) return;

    // 如果到最后一张了，回到第一张
    if (currentIndex.value >= wikiList.value.length - 1) {
      currentIndex.value = 0;
    } else {
      currentIndex.value++;
    }

    // 计算滚动的距离并赋值
    const targetX = carouselRef.value.offsetWidth * 0.88 * currentIndex.value;
    carouselRef.value.scrollTo({ left: targetX, behavior: 'smooth' });
  }, 4000); // 4秒转一次
}

function stopAutoPlay() {
  if (timer) clearInterval(timer);
}

async function loadTaskStats(mid) {
  try {
    const tasks = await apiGet(`/tasks?member_id=${mid}`);
    taskStats.value = {
      total: tasks.length,
      done: tasks.filter(t => t.done).count || tasks.filter(t => t.done).length
    };
  } catch (e) {
    taskStats.value = { total: 0, done: 0 };
  }
}

// 2. BMI 状态计算
const activeMember = computed(() => members.value.find(m => m.id === activeMemberId.value));

const bmiInfo = computed(() => {
  const m = activeMember.value;
  if (!m || !m.height || !m.weight) return { val: 0, status: '未知', color: '#ccc', pos: 0 };

  const h = m.height / 100;
  const val = (m.weight / (h * h)).toFixed(1);

  let status = '正常';
  let color = '#10b981'; // 绿
  let pos = (val - 15) / (35 - 15) * 100; // 计算在进度条上的百分比位置

  if (val < 18.5) { status = '偏瘦'; color = '#3498db'; }
  else if (val > 24 && val <= 28) { status = '偏胖'; color = '#f1c40f'; }
  else if (val > 28) { status = '肥胖'; color = '#e74c3c'; }

  return { val, status, color, pos: Math.min(Math.max(pos, 0), 100) };
});

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
    loadWikiRecommend();

    startAutoPlay();

    // 给容器手动加个监听，更新圆点
    if (carouselRef.value) {
      carouselRef.value.addEventListener('scroll', handleScroll);
    }

  } catch (e) {
    console.error("首页数据加载失败", e);
    userName.value = "请先登录";
  }
});

onBeforeUnmount(() => {
  stopAutoPlay();
  if (carouselRef.value) {
    carouselRef.value.removeEventListener('scroll', handleScroll);
  }
});

// 3. 核心：监听成员切换
watch(activeMemberId, (newId) => {
  if (newId) {
    localStorage.setItem(LS_MEMBER_KEY, newId); // 全局同步钥匙
    loadPreviewData(newId); // 重新加载下方的建议
    loadFilteredHistory(newId);
    loadTaskStats(newId); // 👈 联动任务统计
    loadWikiRecommend();
  }
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

async function loadFilteredHistory(mid) {
  if (!mid) return;
  try {
    // 👇 向后端请求时，带上 member_id 参数
    const sessions = await apiGet(`/consult/sessions?member_id=${mid}`);
    consultHistory.value = sessions.slice(0, 3); // 首页还是只看最近两条
  } catch (e) {
    console.error("加载成员历史失败");
    consultHistory.value = [];
  }
}

function goHistoryConsult(session) {
  // session 是你循环里的那个对象 h
  console.log("正在准备跳转到历史问诊:", session.id);

  router.push({
    path: '/consult',
    query: {
      session_id: session.id,    // 后端的会话ID
      member_id: session.member_id // 对应的成员ID
    }
  });
}

const currentCategory = computed(() => {
  const m = members.value.find(x => x.id === activeMemberId.value);
  if (!m) return "common";

  // 判定优先级：孕妇 > 儿童 > 老年 > 通用
  if (m.special_status === 'pregnant') return "pregnant";
  if (m.age > 0 && m.age <= 12) return "child";
  if (m.age >= 60) return "elder";

  return "common";
});

// 2. 获取推荐文章的函数
async function loadWikiRecommend() {
  // 👇👇👇 核心防御：如果成员列表还是空的，或者还没选中人，先不查推荐 👇👇👇
  if (!activeMemberId.value || members.value.length === 0) {
    console.log("⏳ 成员数据尚未就绪，稍后重试...");
    return;
  }

  try {
    const cat = currentCategory.value; // 拿到计算出来的分类
    const res = await apiGet(`/wiki/recommend?category=${cat}`);
    
    if (res && res.length > 0) {
      wikiList.value = res;
    } else {
      // 即使成功但没数据，也走保底
      const allRes = await apiGet("/wiki");
      wikiList.value = allRes.slice(0, 5);
    }
  } catch (e) {
    // 只有真正的网络错误才会到这里
    console.error("❌ 推荐接口调用失败，正在加载全量百科...");
    const allRes = await apiGet("/wiki");
    wikiList.value = allRes.slice(0, 5);
  }
}

const formatCategory = (cat) => {
  const map = {
    child: "育儿",
    pregnant: "母婴",
    elder: "康养",
    common: "生活"
  };
  return map[cat] || "健康";
};

</script>

<style scoped>
/* 顶部背景 */
.top-bg {
  background: linear-gradient(0deg, #f5f9f8 0%, #dff5ef 100%);
  width: 100%; /* 👈 必须是 100% */
  box-sizing: border-box;

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
  margin-left: 16px !important;
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

.dashboard {
  width: auto;
  margin: 15px 20px;
  box-sizing: border-box;
  /* 💡 关键：左右给 16px padding */
  
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 15px;
  /* ❌ 删掉原本的 margin-bottom: -15px，改用正数 */
  margin-bottom: 20px; 
}

/* 2. 修正小卡片：统一高度和重心 */
.dash-item {
  background: #fff;
  border: 1px solid #eef5f5;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  /* 💡 核心：所有内容水平居中 */
  justify-content: center;
  /* 💡 核心：所有内容垂直居中 */
  width: 100%;
  height: 145px;
  /* 💡 核心：强行固定一个高度，确保排成一排 */
  box-sizing: border-box;
  box-shadow: 0 2px 8px rgba(23, 162, 162, 0.03);
}

.dash-label {
  font-size: 11px;
  color: #8a9999;
  font-weight: 900;
  margin-bottom: auto;
  margin-top: 10px;
  /* 把标签推到最顶 */
}

.dash-status {
  margin-top: auto;
  /* 把状态文字推到最底 */
  font-size: 11px;
  font-weight: 800;
  margin-bottom: 10px;
}

/* BMI 样式 */
.bmi-value {
  font-size: 18px;
  font-weight: 900;
  margin: 4px 0;
}

.bmi-bar-bg {
  width: 90%;
  /* 不要占满 100%，留点呼吸感 */
  height: 4px;
  background: linear-gradient(to right, #3498db, #10b981, #f1c40f, #e74c3c);
  border-radius: 2px;
  position: relative;
  margin: 10px 0 6px;
}

.bmi-pointer {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  position: absolute;
  top: -1px;
  transform: translateX(-50%);
  border: 1px solid #fff;
}

/* 风险标签样式 */
.risk-tags {
  display: flex;
  flex-direction: column;
  /* 👈 关键：改为垂直排列，让字有足够的水平空间 */
  align-items: center;
  /* 居中 */
  gap: 6px;
  /* 标签间距大一点 */
  width: 100%;
  margin: 6px 0;
}

/* 2. 重点优化单个标签：更有分量 */
.risk-dot {
  width: 85%;
  /* 宽度占格子的 85%，看起来更有条状感 */
  font-size: 11px;
  /* 字号稍微调大 1-2px */
  padding: 4px 0;
  /* 增加上下内边距 */
  border-radius: 6px;
  /* 稍微硬朗一点的圆角 */
  color: #fff;
  font-weight: 800;
  /* 字体加粗，增强可读性 */
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  /* 淡淡的投影让字“浮”起来 */

  /* 💡 增加一个点缀 */
  display: flex;
  justify-content: center;
  align-items: center;
}

.lv-3 {
  background: #e74c3c;
}

/* 高危红 */
.lv-2 {
  background: #f39c12;
}

/* 橙色 */
.lv-1 {
  background: #3498db;
}

/* 蓝色 */
.none-text {
  font-size: 10px;
  color: #ccc;
  margin-top: 10px;
}

/* 任务圆环样式 */
.task-circle {
  width: 34px;
  height: 34px;
  border: 3px solid #17a2a2;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 4px 0;
}

.task-num {
  font-size: 11px;
  font-weight: bold;
  color: #17a2a2;
}

.dash-status {
  font-size: 10px;
  color: #333;
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
  width: auto;
  margin: 15px 20px;
  box-sizing: border-box;
  /* 💡 这里不要用负 margin，直接 16px padding */
  margin-top: 0; /* 清除负边距 */
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

/* 修改个性化建议的列表项样式 */
.mini {
  border: 1px solid #e6f2f2;
  background: #ffffff;
  border-radius: 6px;
  padding: 8px;
  margin-bottom: 8px;

  /* 👇👇👇 核心修复：把鼠标变成小手 👇👇👇 */
  cursor: pointer;

  /* 💡 增加一个平滑的过渡效果 */
  transition: all 0.2s ease;
}

/* 💡 顾问建议：增加一个悬浮效果，让用户感觉它“被点亮了” */
.mini:hover {
  background: #f0fafa;
  /* 悬浮时颜色稍微变浅蓝一点点 */
  border-color: #17a2a2;
  /* 边框变成主色调 */
  transform: translateX(4px);
  /* 轻轻向右移动一点，产生互动感 */
}

/* 💡 增加点击瞬间的反馈 */
.mini:active {
  transform: scale(0.98);
  /* 点击瞬间微微缩小，像被按下去一样 */
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

/* 💡 顾问建议：增加一个悬浮效果，让用户感觉它“被点亮了” */
.history-item:hover {
  background: #f0fafa;
  /* 悬浮时颜色稍微变浅蓝一点点 */
  border-color: #17a2a2;
  /* 边框变成主色调 */
  transform: translateX(4px);
  /* 轻轻向右移动一点，产生互动感 */
}

/* 💡 增加点击瞬间的反馈 */
.history-item:active {
  transform: scale(0.98);
  /* 点击瞬间微微缩小，像被按下去一样 */
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
.wiki-section {
  width: auto;
  box-sizing: border-box;
  /* 💡 给这个大容器也加上 16px 左右间距 */
  margin-top: 16px;

  background: #fff;
  border-radius: 24px;
  /* 左右不给padding，让轮播图能贴边滑 */
  box-shadow: 0 10px 30px rgba(23, 162, 162, 0.05);
}

.wiki-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px 12px;
  cursor: pointer;
}

.wiki-title {
  font-size: 16px;
  font-weight: 900;
  color: #123;
}

.wiki-arrow {
  font-size: 12px;
  color: #17a2a2;
  font-weight: bold;
}

/* 轮播容器 */
.wiki-carousel {
  display: flex;
  overflow-x: auto;
  /* 💡 核心：强制水平吸附 */
  scroll-snap-type: x mandatory;
  /* 💡 核心：让滚动变平滑，JS切换时才有动画 */
  scroll-behavior: smooth;
  scrollbar-width: none;
  padding: 0;
  width: 100%;
  gap: 12px;
}

.wiki-carousel::-webkit-scrollbar {
  display: none;
}

/* 2. 幻灯片卡片 */
.wiki-slide {
  flex: 0 0 88%;
  /* 宽度占 88% */
  height: 160px;
  /* 稍微拉高一点，更有气势 */
  border-radius: 20px;
  position: relative;
  overflow: hidden;
  /* 💡 核心：停止时停留在卡片中心 */
  scroll-snap-align: center;
}

/* 3. 新增：底部圆点指示器样式 */
.dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 15px; /* 加大间距 */
  height: 10px;    /* 给个固定高度 */
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #cbdadb; /* 默认灰色调深一点 */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dot.active {
  width: 18px;        /* 选中时变长 */
  background: #17a2a2; /* 选中时变主色调 */
  border-radius: 10px;
}

.slide-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 💡 蒙层：从底部往上渐黑 */
.slide-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 70%;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, transparent 100%);
}

.slide-info {
  position: absolute;
  bottom: 12px;
  left: 16px;
  right: 16px;
  color: #fff;
}

.slide-tag {
  font-size: 10px;
  background: rgba(23, 162, 162, 0.8);
  display: inline-block;
  padding: 2px 8px;
  border-radius: 6px;
  margin-bottom: 4px;
}

.slide-h1 {
  font-size: 15px;
  font-weight: 800;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.me-page, .page-root { 
  /* 💡 这里的类名请对应你 template 最外层的那个 div */
  height: 100vh;           /* 占满屏幕高度 */
  overflow-y: auto;        /* 👈 关键：开启纵向滚动 */
  overflow-x: hidden;      /* 禁止横向溢出 */
  display: flex;
  flex-direction: column;
  background: linear-gradient(0deg, #f5f9f8 0%, #dff5ef 100%);
  scroll-behavior: smooth; /* 让点击跳转时的滚动变丝滑 */
}

.home-container {
  /* 💡 核心修复：锁死宽度为 100%，且内边距算在宽度内 */
  width: 100%;
  max-width: 450px;        /* 保持手机预览感 */
  box-sizing: border-box;  /* 👈 必须加这一行，让 padding 不撑大盒子 */
  margin: 0 auto;         /* 在电脑端居中 */
  
  height: 100vh;
  overflow-y: auto;        /* 开启滚动 */
  overflow-x: hidden;      /* 👈 物理屏蔽：绝对不准产生左右晃动 */
  
  display: flex;
  flex-direction: column;
  background: linear-gradient(0deg, #f5f9f8 0%, #dff5ef 100%);
  padding: 0;              /* 👈 这里设为 0，留白交给里面的组件自己控制 */
}

/* 2. 隐藏滚动条（让它看起来像原生 App） */
.home-container::-webkit-scrollbar {
  display: none;
}

/* 3. 增强底部安全区：极其重要！ */
/* 确保滚动到最下面时，内容不会被底部的 TabBar 挡住 */
.safe-bottom {
  height: 70px;           /* 留出约 100px 的空白 */
  flex-shrink: 0;          /* 防止被 flex 压缩 */
}

/* 4. 给每一个大模块增加一点间距，增加“饱满感” */
.top-bg, .dashboard, .content, .wiki {
  flex-shrink: 0;          /* 👈 关键：保证在滚动容器内不会被挤扁 */
  margin-bottom: 12px;
}
</style>
