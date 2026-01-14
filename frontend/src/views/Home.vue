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

// 1. 任务进度计算
const taskStats = ref({ total: 0, done: 0 });

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
    loadFilteredHistory(newId);
    loadTaskStats(newId); // 👈 联动任务统计
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

.dashboard {
  display: grid;
  /* 💡 关键：使用 1fr 1fr 1fr，强行让三列平均分配宽度，不被内容撑开 */
  grid-template-columns: repeat(3, 1fr); 
  gap: 10px;
  padding: 0 16px; /* 加大两边的 Margin，让它和顶部的头像栏对齐 */
  margin-top: 15px;
  margin-bottom: -15px;
  margin-right: 24px;
  margin-left: -4px;
}

/* 2. 修正小卡片：统一高度和重心 */
.dash-item {
  background: #fff;
  border: 1px solid #eef5f5;
  border-radius: 16px;
  padding: 12px 8px; /* 减小左右 padding，防止内部内容挤爆 */
  
  display: flex;
  flex-direction: column;
  align-items: center;      /* 💡 核心：所有内容水平居中 */
  justify-content: center;   /* 💡 核心：所有内容垂直居中 */
  
  height: 145px;            /* 💡 核心：强行固定一个高度，确保排成一排 */
  box-sizing: border-box;
  box-shadow: 0 2px 8px rgba(23,162,162,0.03);
}

.dash-label {
  font-size: 11px;
  color: #8a9999;
  font-weight: 900;
  margin-bottom: auto; /* 把标签推到最顶 */
}

.dash-status {
  margin-top: auto;   /* 把状态文字推到最底 */
  font-size: 11px;
  font-weight: 800;
}

/* BMI 样式 */
.bmi-value { font-size: 18px; font-weight: 900; margin: 4px 0; }
.bmi-bar-bg {
  width: 90%;               /* 不要占满 100%，留点呼吸感 */
  height: 4px;
  background: linear-gradient(to right, #3498db, #10b981, #f1c40f, #e74c3c);
  border-radius: 2px;
  position: relative;
  margin: 10px 0 6px;
}
.bmi-pointer {
  width: 6px; height: 6px; border-radius: 50%;
  position: absolute; top: -1px; transform: translateX(-50%);
  border: 1px solid #fff;
}

/* 风险标签样式 */
.risk-tags {
  display: flex;
  flex-direction: column;   /* 👈 关键：改为垂直排列，让字有足够的水平空间 */
  align-items: center;      /* 居中 */
  gap: 6px;                 /* 标签间距大一点 */
  width: 100%;
  margin: 6px 0;
}

/* 2. 重点优化单个标签：更有分量 */
.risk-dot {
  width: 85%;               /* 宽度占格子的 85%，看起来更有条状感 */
  font-size: 11px;          /* 字号稍微调大 1-2px */
  padding: 4px 0;           /* 增加上下内边距 */
  border-radius: 6px;       /* 稍微硬朗一点的圆角 */
  color: #fff;
  font-weight: 800;         /* 字体加粗，增强可读性 */
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* 淡淡的投影让字“浮”起来 */
  
  /* 💡 增加一个点缀 */
  display: flex;
  justify-content: center;
  align-items: center;
}
.lv-3 { background: #e74c3c; } /* 高危红 */
.lv-2 { background: #f39c12; } /* 橙色 */
.lv-1 { background: #3498db; } /* 蓝色 */
.none-text { font-size: 10px; color: #ccc; margin-top: 10px; }

/* 任务圆环样式 */
.task-circle {
  width: 34px; height: 34px;
  border: 3px solid #17a2a2;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  margin: 4px 0;
}
.task-num { font-size: 11px; font-weight: bold; color: #17a2a2; }
.dash-status { font-size: 10px; color: #333; }

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
