<template>
  <PageShell tab="consult">
    <div class="consult-page">
      <!-- 顶部导航 -->
      <div class="nav">
        <!-- 1. 左侧容器 -->
        <div class="nav-side-box">
          <button class="icon-btn" @click="onDoctorClick">🩺</button>
        </div>

        <!-- 2. 中间标题 -->
        <div class="nav-title">
          <div class="t1">AI 问诊</div>
          <div class="t2">选择类别后开始对话</div>
        </div>

        <!-- 3. 右侧容器 -->
        <div class="nav-side-box right">
          <button class="icon-btn" @click="handleManualNewSession">➕</button>
          <button class="icon-btn" @click="openHistory">🕘</button>
        </div>
      </div>

      <!-- 类别选择 -->
      <div class="modes">
        <button v-for="m in modes" :key="m.key" class="mode" :class="{ on: mode === m.key }" @click="setMode(m.key)">
          <span class="ico">{{ m.ico }}</span>
          <span class="txt">{{ m.label }}</span>
        </button>
      </div>

      <div class="action-bar">
        <button class="gen-plan-btn" @click="handleGeneratePlan"
          :disabled="isGenerating || (currentSession?.messages?.length || 0) < 2">
          <span v-if="!isGenerating">🪄 结束问诊并生成健康方案</span>
          <span v-else>正在生成专家方案...</span>
        </button>
      </div>

      <!-- 消息区 -->
      <div ref="msgBox" class="msgs">
        <div v-for="msg in (currentSession?.messages || [])" :key="msg.id" class="row" :class="msg.role">
          <div class="bubble">
            <div class="meta">
              <span class="who">{{ msg.role === 'user' ? '我' : 'AI' }}</span>
              <span class="time">{{ msg.time }}</span>
            </div>

            <!-- 文本消息 -->
            <div v-if="msg.type === 'text'" class="text" v-text="msg.text"></div>

            <!-- 图片消息 -->
            <div v-else-if="msg.type === 'image'" class="img-wrap">
              <img :src="msg.imageDataUrl" alt="upload" />
              <div v-if="msg.text" class="img-caption" v-text="msg.text"></div>
            </div>
          </div>
        </div>

        <div v-if="loading" class="row ai">
          <div class="bubble">
            <div class="meta"><span class="who">AI</span><span class="time">...</span></div>
            <div class="text">正在分析中…</div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="inputbar">
        <button class="plus" @click="togglePlusMenu" title="更多">
          ＋
        </button>

        <textarea v-model="input" class="input" rows="2" placeholder="描述症状：持续多久？是否发热/腹痛/咳嗽？有无基础病/用药？"
          @keydown.enter.exact.prevent="sendText" />

        <button class="send" :disabled="!canSend" @click="sendText">
          {{ loading ? "…" : "发送" }}
        </button>

        <!-- + 菜单 -->
        <div v-if="plusMenu" class="plus-menu" @click.stop>
          <button class="menu-item" @click="triggerImageUpload">
            🖼️ 上传图片
          </button>
          <button class="menu-item" @click="onVoiceToText">
            🎙️ 语音转文字（预留）
          </button>
        </div>

        <!-- 隐藏 file input -->
        <input ref="fileInput" type="file" accept="image/*" class="file" @change="onFileChange" />
      </div>

      <!-- ✅ 给 PageShell tabbar 留安全区（不改 PageShell） -->
      <div class="safe-bottom"></div>

      <!-- 历史记录弹层 -->
      <div v-if="historyOpen" class="mask" @click.self="closeHistory">
        <div class="sheet">
          <div class="sheet-head">
            <div class="sheet-title">历史聊天记录</div>
            <div class="sheet-actions">
              <button class="btn ghost" @click="newSession">新建会话</button>
              <button class="btn" @click="closeHistory">关闭</button>
            </div>
          </div>

          <div class="sheet-list">
            <div v-for="s in sessions" :key="s.id" class="session" :class="{ on: s.id === currentSessionId }"
              @click="loadSession(s.id)">
              <div class="session-top">
                <div class="session-title">
                  {{ modeLabel(s.mode) }} · {{ s.title || '未命名会话' }}
                </div>
                <button class="btn-del-session" @click.stop="confirmDeleteSession(s)">
                  🗑️
                </button>
                <div class="session-time">{{ s.updatedAt }}</div>
              </div>
              <div class="session-sub">
                {{ s.preview || '（暂无内容）' }}
              </div>
            </div>
          </div>

          <div class="sheet-foot">
            <button class="btn danger" @click="clearAllSessions">清空全部（本地）</button>
          </div>
        </div>
      </div>

      <div v-if="isGenerating" class="loading-overlay">
        <div class="loader-box">
          <div class="spinner"></div>
          <p>AI 医生正在复盘对话...</p>
          <p class="sub-hint">正在为您定制专属健康方案</p>
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch } from "vue";
import PageShell from "../components/PageShell.vue";
import { apiPost, getToken, apiGet } from '../api/http';
import { useRouter, useRoute } from "vue-router";

const LS_MEMBER_KEY = "active_member_id";
const router = useRouter();
const route = useRoute();
const isGenerating = ref(false);

function handleManualNewSession() {
  // 1. 构造一个全新的前端会话对象
  const newShell = {
    id: uid(),           // 前端用的随机 ID
    serverId: null,      // 👈 重要！标记此会话还没在数据库挂号
    mode: mode.value,    // 继承当前的模式（常用/儿童等）
    title: "新问诊会话",
    updatedAt: nowDateTime(),
    preview: "（尚未开始）",
    messages: [{
      id: uid(),
      role: "ai",
      type: "text",
      time: nowTime(),
      text: "你好，我是AI问诊助手。请描述你的症状，我会为你分析。"
    }]
  };

  // 2. 把新会话塞到列表最前面
  sessions.value.unshift(newShell);

  // 3. 切换到这个新会话
  currentSessionId.value = newShell.id;

  // 4. 保存一下“本子”的现状，关闭历史弹层
  saveSessions();
  historyOpen.value = false;

  // 5. 滚动到顶部（欢迎语）
  scrollToBottom();

  console.log("📝 已开启新画布，等待用户首句发言后领号...");
}

async function handleGeneratePlan() {
  // 1. 获取后端会话 ID (对应你数据库里的 ConsultSession.id)
  // 💡 注意：这里确保你之前存入的变量名是正确的，比如叫 currentSessionId 还是 backendSessionId
  const sid = currentSession.value.serverId;

  if (!sid) {
    alert("当前会话尚未建立，请先发送一条消息。");
    return;
  }

  // 2. 确认弹窗
  if (!confirm("确定结束本次咨询并生成健康方案吗？")) return;

  // 3. 开启加载状态
  isGenerating.value = true;

  try {
    // 4. 调用我们刚才写好的后端生成接口
    const res = await apiPost(`/consult/${sid}/generate_plan`, {});

    if (res.ok) {
      alert(`🎉 方案生成成功！\nAI 医生为您制定了 ${res.count_advice} 条新建议。`);

      // 5. 【高光时刻】：自动跳转到建议页查看成果
      router.push('/advice');
    }
  } catch (e) {
    console.error("生成方案失败", e);
    alert("生成方案时遇到一点小意外，请重试。");
  } finally {
    isGenerating.value = false;
  }
}

// ====== 唯一合法的初始化挂载 ======
onMounted(async () => {
  console.log("🚀 正在初始化问诊室...");

  try {
    // --- 第一步：对账（清理本地已失效的记录）保持现状 ---
    const serverSessions = await apiGet("/consult/sessions");
    const serverIds = serverSessions.map(s => s.id);
    const localData = loadSessions();

    const syncedSessions = localData.filter(localSess => {
      if (!localSess.serverId) return true; 
      return serverIds.includes(localSess.serverId);
    });
    sessions.value = syncedSessions;

    // --- 第二步：逻辑分流（这是你要的改动） ---
    const historySessionId = route.query.session_id; // 从 URL 获取历史 ID

    if (historySessionId) {
      // 场景 A：从首页点历史记录进来的
      console.log("📂 正在恢复指定的历史记录:", historySessionId);
      // 在同步后的列表里找这一条
      const found = sessions.value.find(s => s.serverId == historySessionId);
      if (found) {
        currentSessionId.value = found.id;
      } else {
        // 如果本地没存这段话（比如换了浏览器），调接口拿
        await loadExistingSession(historySessionId);
      }
    } else {
      // 场景 B：直接点 Tab 进来的 -> 【强制开新局，且不领号】
      console.log("📝 准备好一张空白问诊单...");
      const shell = {
        id: uid(),
        serverId: null, // 👈 说话时再领号，现在数据库里什么都不会增加
        mode: mode.value,
        title: "新问诊会话",
        messages: defaultWelcomeMessages(),
        updatedAt: nowDateTime(),
        preview: "（新问诊）"
      };
      
      // 把新白纸插到最前面，并设为当前活跃
      sessions.value.unshift(shell);
      currentSessionId.value = shell.id;
    }

    saveSessions(); // 存一下对账和开局后的结果

  } catch (e) {
    console.warn("⚠️ 初始化失败，将使用本地缓存", e);
    sessions.value = loadSessions();
  }

  // --- 第三步：监听与滚动 ---
  window.addEventListener("click", onGlobalClick);
  scrollToBottom();
});

/**
 * 辅助函数：如果本地没缓存这对话，从后端抓
 */
async function loadExistingSession(sid) {
  try {
    const msgs = await apiGet(`/consult/${sid}/messages`);
    const s = {
      id: uid(),
      serverId: sid,
      mode: "common",
      title: "历史追溯",
      updatedAt: nowDateTime(),
      messages: msgs.map(m => ({
        id: m.id, role: m.role, type: "text", text: m.content, time: "历史"
      }))
    };
    sessions.value.unshift(s);
    currentSessionId.value = s.id;
  } catch (e) {
    console.error("抓取历史失败");
  }
}

function startTemporarySession() {
  // 1. 构造一个 serverId 为 null 的“虚拟本子”
  const tempSess = {
    id: uid(),           // 前端用的 UUID
    serverId: null,      // 👈 重点：现在是空的，数据库里还没它
    mode: mode.value,
    title: "新问诊会话",
    updatedAt: nowDateTime(),
    preview: "（尚未开始）",
    messages: [{
      id: uid(),
      role: "ai",
      type: "text",
      time: nowTime(),
      text: "你好，我是AI问诊助手。请描述你的症状，我会为你分析。"
    }]
  };

  // 2. 将这个虚拟本子设为当前活跃页面
  // 💡 注意：我们不需要把它 unshift 进 sessions 列表，
  // 只有当用户说话领号后，再塞进列表存 localStorage
  currentSessionId.value = tempSess.id;
  
  // 我们建立一个临时的活跃对象
  // 假设你的 sessions 是一个 ref 数组
  sessions.value = [tempSess, ...sessions.value]; 
  
  console.log("✨ 虚拟页面已就绪，等待首句发言后触发后端注册。");
}

/** ============ 配置：四类模式 ============ */
const modes = [
  { key: "common", label: "常用", ico: "💬", prompt: "你是全科医生..." },
  { key: "child", label: "儿童", ico: "🧒", prompt: "你是儿科医生..." },
  { key: "pregnant", label: "孕妇", ico: "🤰", prompt: "你是产科医生..." },
  { key: "elder", label: "老年", ico: "👴", prompt: "你是老年医生..." },
];
const mode = ref("common");

const modeHint = computed(() => {
  switch (mode.value) {
    case "child":
      return "儿童：建议补充年龄/体重、精神状态、体温、是否呕吐腹泻、饮水进食情况。";
    case "pregnant":
      return "孕妇：建议补充孕周、胎动变化、是否见红/腹痛、血压与既往产科史。";
    case "elder":
      return "老年：建议补充基础病/长期用药、血压血糖、胸闷气促/跌倒等危险信号。";
    default:
      return "常用：建议补充持续时间、诱因、加重/缓解因素、既往史与用药情况。";
  }
});

function modeLabel(k) {
  return modes.find(m => m.key === k)?.label ?? "常用";
}

/** ============ 预留接口：接入真实医生 ============ */
function onDoctorClick() {
  // TODO: 未来接入真实医生：跳转医生列表/挂号/在线咨询等
  console.log("[TODO] 接入真实医生");
}

/** ============ 历史会话（本地存储） ============ */
const LS_KEY = "consult_sessions_v1";

function nowTime() {
  const d = new Date();
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}
function nowDateTime() {
  const d = new Date();
  const M = String(d.getMonth() + 1).padStart(2, "0");
  const D = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${M}/${D} ${hh}:${mm}`;
}
function uid() {
  try { return crypto.randomUUID(); }
  catch { return "id_" + Math.random().toString(16).slice(2) + Date.now().toString(16); }
}
function defaultWelcomeMessages() {
  return [
    {
      id: uid(),
      role: "ai",
      type: "text",
      time: nowTime(),
      text: "你好，我是AI问诊助手。请描述你的主要不适，并补充持续时间与是否有基础病/用药。",
    },
  ];
}


function loadSessions() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}
function saveSessions() {
  localStorage.setItem(LS_KEY, JSON.stringify(sessions.value));
}

const sessions = ref(loadSessions());
const currentSessionId = ref("");

// 👇 2. 核心修改：确保当前会话有“后端ID”
// 如果是老数据没有 serverId，或者新会话，都需要去后端申请一个
async function ensureBackendSession(session) {
  // 如果已经领过号了（serverId有值），直接用
  if (session.serverId) return session.serverId;

  // 如果 serverId 是 null，说明是刚才点 ➕ 号新建的，现在去后端注册
  const mid = localStorage.getItem("active_member_id") || 1;
  console.log("🚀 用户开口说话了，正在前往后端领取唯一 ID...");

  try {
    const res = await apiPost(`/consult/sessions?member_id=${mid}`, {});
    session.serverId = res.id; // 拿到真 ID (比如 105)
    saveSessions(); // 存进本地记忆
    return session.serverId;
  } catch (e) {
    alert("问诊室开启失败，请检查网络");
    throw e;
  }
}

async function confirmDeleteSession(s) {
  // 1. 获取后端真实 ID
  const sid = s.serverId;

  if (!sid) {
    // 如果这一条记录根本没传到后端（比如只是本地生成的空白），直接本地删了就行
    sessions.value = sessions.value.filter(item => item.id !== s.id);
    return;
  }

  if (!confirm("确定要永久删除这条问诊记录吗？")) return;

  try {
    // 2. 【核心修改】这里确保传的是数字 ID
    const resp = await fetch(`http://127.0.0.1:8000/api/consult/sessions/${sid}`, {
      method: 'DELETE',
      headers: {
        "Authorization": `Bearer ${getToken()}`
      }
    });

    if (resp.ok) {
      // 3. 成功后，按前端 UUID 过滤列表，界面同步更新
      sessions.value = sessions.value.filter(item => item.id !== s.id);

      if (s.id === currentSessionId.value) {
        currentSessionId.value = "";
      }
      console.log("后端记录已成功删除");
    } else {
      const err = await resp.json();
      alert("删除失败：" + err.detail);
    }
  } catch (e) {
    alert("网络错误");
  }
}

function ensureSession() {
  if (sessions.value.length === 0) {
    const s = {
      id: uid(),
      mode: mode.value,
      title: "会话 1",
      updatedAt: nowDateTime(),
      preview: "你好，我是AI问诊助手…",
      messages: defaultWelcomeMessages(),
    };
    sessions.value.unshift(s);
    currentSessionId.value = s.id;
    saveSessions();
  } else if (!currentSessionId.value) {
    currentSessionId.value = sessions.value[0].id;
  }
}

ensureSession();

const currentSession = computed(() => {
  return sessions.value.find(s => s.id === currentSessionId.value) || sessions.value[0];
});

onMounted(() => {
  ensureSession();
});


function touchSessionPreview() {
  const s = currentSession.value;
  const lastUser = [...s.messages].reverse().find(m => m.role === "user");
  s.preview = lastUser?.type === "text"
    ? lastUser.text.slice(0, 40)
    : lastUser?.type === "image"
      ? "（图片）"
      : s.preview;

  s.updatedAt = nowDateTime();
  saveSessions();
}

// 👇 3. 新建会话时，不立刻请求后端，等发消息时再请求（懒加载），防止产生大量空会话
async function newSession() {
  const idx = sessions.value.length + 1;
  const s = {
    id: uid(), // 前端路由用的 UUID
    serverId: null, // ⏳ 等待连接后端分配
    mode: mode.value,
    title: `会话 ${idx}`,
    updatedAt: nowDateTime(),
    preview: "（暂无内容）",
    messages: defaultWelcomeMessages(),
  };
  sessions.value.unshift(s);
  currentSessionId.value = s.id;
  saveSessions();
  historyOpen.value = false;
  scrollToBottom();
}

function loadSession(id) {
  currentSessionId.value = id;
  historyOpen.value = false;
  scrollToBottom();
}

function clearAllSessions() {
  sessions.value = [];
  currentSessionId.value = "";
  saveSessions();
  ensureSession();
  historyOpen.value = false;
  scrollToBottom();
}

/** ============ 模式切换 ============ */
function setMode(k) {
  mode.value = k;
  // 可选：给当前会话记录一个“系统提示”
  currentSession.value.mode = k;
  currentSession.value.messages.push({
    id: uid(),
    role: "ai",
    type: "text",
    time: nowTime(),
    text: `已切换到「${modeLabel(k)}」模式。${modeHint.value}`,
  });
  touchSessionPreview();
  scrollToBottom();
}

/** ============ 历史弹层 ============ */
const historyOpen = ref(false);

function openHistory() {
  historyOpen.value = true;
}
function closeHistory() {
  historyOpen.value = false;
}

/** ============ 消息发送 ============ */
const msgBox = ref(null);
const input = ref("");
const loading = ref(false);

const canSend = computed(() => input.value.trim().length > 0 && !loading.value);

async function sendText() {
  const text = input.value.trim();
  if (!text || loading.value) return;

  // 1. 前端UI立刻上屏
  currentSession.value.messages.push({
    id: uid(), role: "user", type: "text", time: nowTime(), text
  });
  input.value = "";
  touchSessionPreview();
  scrollToBottom();

  loading.value = true;

  try {
    // 2. 确保有后端的 SessionID
    const serverId = await ensureBackendSession(currentSession.value);
    if (!serverId) {
      throw new Error("无法连接到服务器，请检查网络或后端服务");
    }

    // 3. 构建 Prompt (实现你的专科路由逻辑)
    // 技巧：把当前模式对应的 Prompt 拼接到用户内容前面，或者通过 system 角色发送
    // 这里我们简单粗暴地拼接，让 AI 知道它的身份
    const currentModeConfig = modes.find(m => m.key === mode.value);
    const systemInstruction = currentModeConfig ? `【系统指令：${currentModeConfig.prompt}】\n` : "";

    // 如果是该会话的第一句话，带上 System Prompt，否则只发内容
    // 简单起见，我们每次都带上模式标记，让 AI 保持人设
    const finalContent = `${systemInstruction}用户描述：${text}`;

    // 4. 调用后端 API
    // 注意：这里用的是我们刚测通的 /chat 接口
    const res = await apiPost(`/consult/${serverId}/chat?content=${encodeURIComponent(finalContent)}`, {});

    // 5. 后端返回结果上屏
    currentSession.value.messages.push({
      id: uid(),
      role: "ai",
      type: "text",
      time: nowTime(),
      text: res.content // 后端返回的 JSON 里 content 字段
    });

    saveSessions(); // 保存聊天记录到本地

  } catch (err) {
    console.error(err);
    currentSession.value.messages.push({
      id: uid(), role: "ai", type: "text", time: nowTime(),
      text: `(发送失败: ${err.message || '网络错误'})`
    });
  } finally {
    loading.value = false;
    touchSessionPreview();
    scrollToBottom();
  }
}

async function scrollToBottom() {
  await nextTick();
  const el = msgBox.value;
  if (!el) return;
  el.scrollTop = el.scrollHeight;
}

/** ============ + 菜单：图片 / 语音转文字 ============ */
const plusMenu = ref(false);
const fileInput = ref(null);

function togglePlusMenu() {
  plusMenu.value = !plusMenu.value;
}

function triggerImageUpload() {
  plusMenu.value = false;
  fileInput.value?.click();
}

function onVoiceToText() {
  plusMenu.value = false;
  // TODO: 预留语音转文字：打开录音、调用 STT，写回 input
  console.log("[TODO] 语音转文字（STT）");
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function onFileChange(e) {
  const file = e.target.files?.[0];
  e.target.value = "";
  if (!file) return;

  plusMenu.value = false;

  const dataUrl = await fileToDataUrl(file);

  // 先把图片消息插入对话
  currentSession.value.messages.push({
    id: uid(),
    role: "user",
    type: "image",
    time: nowTime(),
    text: "（上传图片）",
    imageDataUrl: dataUrl,
  });

  touchSessionPreview();
  scrollToBottom();

  loading.value = true;
  try {
    const reply = await callAI(mode.value, { text: "", hasImage: true });
    currentSession.value.messages.push({
      id: uid(),
      role: "ai",
      type: "text",
      time: nowTime(),
      text: reply,
    });
    touchSessionPreview();
  } finally {
    loading.value = false;
    scrollToBottom();
  }
}

/** 点击页面关闭 + 菜单 */
function onGlobalClick() {
  if (plusMenu.value) plusMenu.value = false;
}

onMounted(() => {
  ensureSession();
  scrollToBottom();
  window.addEventListener("click", onGlobalClick);
});
onBeforeUnmount(() => {
  window.removeEventListener("click", onGlobalClick);
});
</script>

<style scoped>
/* 整页：不左右滑；消息区内部滚动 */
.consult-page {
  height: 100%;
  box-sizing: border-box;
  padding: 14px 0 0;
  overflow: hidden;
  overflow-x: hidden;
  display: grid;
  grid-template-rows: auto auto auto 1fr auto auto;
  gap: 10px;
}

/* 顶部导航 */
.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  
  /* 💡 关键：确保 padding 算在宽度内，且宽度不溢出 */
  box-sizing: border-box;
  width: 100%; 
  padding: 8px 12px; /* 内部留一点距离，不让按钮贴边 */
  
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 16px;
}

/* 左右两个侧边盒子的逻辑 */
.nav-side-box {
  width: 80px;      /* 👈 固定一个宽度，保证左右是对称的 */
  display: flex;
  gap: 8px;
}

.nav-side-box.right {
  justify-content: flex-end; /* 👈 让右边的按钮靠最右排队 */
}

/* 中间标题的逻辑 */
.nav-title {
  flex: 1;           /* 👈 占据中间剩下的所有空间 */
  text-align: center;
  min-width: 0;      /* 防止文字太长撑破布局 */
}

.t1 { font-size: 15px; font-weight: 900; color: #123; }
.t2 { font-size: 11px; color: #6b7f7f; margin-top: 2px; }

/* 按钮样式（微调，确保居中） */
.icon-btn {
  width: 32px;       /* 稍微调小一点点，适配小屏幕 */
  height: 32px;
  display: flex;     /* 改用 flex 居中更稳 */
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid #f0f4f4;
  border-radius: 8px;
  cursor: pointer;
  padding: 0;
  font-size: 16px;
  flex-shrink: 0;    /* 👈 关键：不准被挤扁 */
}

/* 类别 */
.modes {
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 10px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.mode {
  border: 1px solid rgba(0, 0, 0, .08);
  background: #fff;
  border-radius: 12px;
  padding: 8px 6px;
  cursor: pointer;
  display: grid;
  justify-items: center;
  gap: 2px;
}

.mode.on {
  border-color: rgba(23, 162, 162, .45);
  background: rgba(23, 162, 162, .10);
}

.mode .ico {
  font-size: 16px;
}

.mode .txt {
  font-size: 11px;
  color: #2a3c3c;
  font-weight: 800;
}

/* 1. 外层容器：负责左右的 Margin */
.action-bar {
  padding: 0 16px;
  /* 左右留白 */
  margin-top: -4px;
  /* 向上靠拢，贴合上面的提示条 */
  margin-bottom: 12px;
  /* 与下方聊天记录拉开一点距离 */
}

/* 2. 按钮本体：小巧、精致、有质感 */
.gen-plan-btn {
  width: 100%;
  /* 宽度撑满容器 */
  height: 38px;
  /* 固定高度，不要太厚 */
  border: none;
  background: linear-gradient(135deg, #17a2a2, #10b981);
  /* 渐变色 */
  color: white;
  border-radius: 12px;
  /* 柔和的圆角 */
  font-size: 13px;
  /* 字体小一点，显专业 */
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(23, 162, 162, 0.15);
  /* 淡阴影 */
  transition: all 0.3s ease;
}

/* 3. 禁用状态（还没怎么聊的时候） */
.gen-plan-btn:disabled {
  background: #f0f4f4;
  /* 浅灰色 */
  color: #aebdbd;
  /* 灰字 */
  box-shadow: none;
  /* 移除阴影 */
  cursor: not-allowed;
}

/* 4. 点击反馈效果 */
.gen-plan-btn:active:not(:disabled) {
  transform: scale(0.98);
  /* 点击时微微缩小 */
  opacity: 0.9;
}

/* 消息区 */
.msgs {
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px;
}

.row {
  display: flex;
  margin: 8px 0;
}

.row.user {
  justify-content: flex-end;
}

.row.ai {
  justify-content: flex-start;
}

.bubble {
  max-width: 82%;
  border-radius: 14px;
  padding: 10px;
  border: 1px solid rgba(0, 0, 0, .06);
  background: #fff;
}

.row.user .bubble {
  background: rgba(23, 162, 162, .10);
  border-color: rgba(23, 162, 162, .20);
}

.meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 11px;
  color: #6b7f7f;
  margin-bottom: 6px;
}

.who {
  font-weight: 900;
  color: #2a3c3c;
}

.text {
  font-size: 13px;
  color: #123;
  white-space: pre-wrap;
}

.img-wrap img {
  width: 100%;
  border-radius: 12px;
  display: block;
  border: 1px solid rgba(0, 0, 0, .06);
}

.img-caption {
  margin-top: 8px;
  font-size: 12px;
  color: #2a3c3c;
  white-space: pre-wrap;
}

/* 输入区 */
.inputbar {
  position: relative;
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 10px;
  display: grid;
  grid-template-columns: 40px 1fr 74px;
  gap: 10px;
  align-items: end;
}

.plus {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(0, 0, 0, .08);
  background: #fff;
  font-size: 18px;
  cursor: pointer;
}

.input {
  width: 100%;
  resize: none;
  box-sizing: border-box;
  border: 1px solid #e7efef;
  border-radius: 12px;
  padding: 10px;
  font-size: 13px;
  outline: none;
}

.input:focus {
  border-color: rgba(23, 162, 162, .55);
}

.send {
  height: 40px;
  border-radius: 12px;
  border: 1px solid #17a2a2;
  background: #17a2a2;
  color: #fff;
  font-weight: 900;
  cursor: pointer;
}

.send:disabled {
  opacity: .55;
  cursor: not-allowed;
}

/* + 菜单 */
.plus-menu {
  position: absolute;
  left: 10px;
  bottom: 58px;
  width: 180px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, .10);
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, .12);
  overflow: hidden;
  z-index: 20;
}

.menu-item {
  width: 100%;
  text-align: left;
  padding: 12px 12px;
  border: none;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}

.menu-item:hover {
  background: rgba(23, 162, 162, .08);
}

.file {
  display: none;
}

/* tabbar 安全区（不改 PageShell） */
.safe-bottom {
  height: 72px;
}

/* 历史弹层 */
.mask {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 64px;
  /* 不盖住 tabbar */
  background: rgba(0, 0, 0, .35);
  display: grid;
  place-items: center;
  z-index: 60;
}

.sheet {
  width: 92%;
  max-height: 84%;
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, .10);
  overflow: hidden;
  display: grid;
  grid-template-rows: auto 1fr auto;
}

.sheet-head {
  padding: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, .06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.sheet-title {
  font-size: 14px;
  font-weight: 900;
  color: #123;
}

.sheet-actions {
  display: flex;
  gap: 8px;
}

.btn {
  border: 1px solid rgba(0, 0, 0, .10);
  background: #fff;
  border-radius: 12px;
  padding: 8px 10px;
  font-size: 12px;
  cursor: pointer;
}

.btn.ghost {
  background: rgba(23, 162, 162, .08);
  border-color: rgba(23, 162, 162, .25);
}

.btn.danger {
  border-color: rgba(226, 59, 59, .35);
  color: #e23b3b;
}

.sheet-list {
  padding: 10px 12px;
  overflow-y: auto;
  overflow-x: hidden;
  display: grid;
  gap: 10px;
}

.session {
  border: 1px solid rgba(0, 0, 0, .08);
  border-radius: 14px;
  padding: 10px;
  cursor: pointer;
}

.session.on {
  border-color: rgba(23, 162, 162, .45);
  background: rgba(23, 162, 162, .08);
}

.session-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
}

.session-title {
  font-weight: 900;
  color: #123;
  font-size: 13px;
}

.session-time {
  font-size: 11px;
  color: #6b7f7f;
  white-space: nowrap;
}

.session-sub {
  margin-top: 6px;
  font-size: 12px;
  color: #4f6464;
}

.btn-del-session {
  background: transparent;
  border: none;
  font-size: 14px;
  cursor: pointer;
  opacity: 0.3;
  transition: all 0.2s;
  padding: 4px;
}

/* 鼠标悬停在卡片上才显示垃圾桶，细节感满满 */
.session:hover .btn-del-session {
  opacity: 1;
  color: #ff4d4f;
}

.btn-del-session:active {
  transform: scale(0.9);
}

.sheet-foot {
  padding: 10px 12px;
  border-top: 1px solid rgba(0, 0, 0, .06);
  display: flex;
  justify-content: flex-end;
}

/* 全屏加载遮罩 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: grid;
  place-items: center;
  z-index: 100;
  backdrop-filter: blur(4px);
}

.loader-box {
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #17a2a2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 15px;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.sub-hint {
  font-size: 12px;
  color: #99a;
  margin-top: 8px;
}
</style>

<!-- 你后面接真实 4 个 AI 接口要改哪里？

就一个地方：callAI(kind, payload) 这个函数里。
你可以按 kind 分发到四个 URL / 四套 prompt / 四个模型。

接入“语音转文字（STT）”要改哪里？

onVoiceToText()：把录音 + STT 结果写回 input.value = '...' 即可。

接入“真实医生”要改哪里？

onDoctorClick()：改成跳转医生页/挂号页/在线问诊页，或打开一个 WebView/外链即可。

如果你把你当前路由文件里 /consult 对应的组件路径贴一下，我也可以顺手给你对齐到你项目目录（避免 import 路径你来回改）。 -->