<template>
  <PageShell tab="consult">
    <div class="consult-page">
      <!-- 顶部导航 -->
      <div class="nav">
        <button class="icon-btn" @click="onDoctorClick" title="接入真实医生（预留）">
          🩺
        </button>

        <div class="nav-title">
          <div class="t1">AI 问诊</div>
          <div class="t2">选择类别后开始对话</div>
        </div>

        <button class="icon-btn" @click="openHistory" title="历史记录">
          🕘
        </button>
      </div>

      <!-- 类别选择 -->
      <div class="modes">
        <button
          v-for="m in modes"
          :key="m.key"
          class="mode"
          :class="{ on: mode === m.key }"
          @click="setMode(m.key)"
        >
          <span class="ico">{{ m.ico }}</span>
          <span class="txt">{{ m.label }}</span>
        </button>
      </div>

      <!-- 提示条 -->
      <div class="hint">
        <span class="dot"></span>
        <span class="hint-text">{{ modeHint }}</span>
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

        <textarea
          v-model="input"
          class="input"
          rows="2"
          placeholder="描述症状：持续多久？是否发热/腹痛/咳嗽？有无基础病/用药？"
          @keydown.enter.exact.prevent="sendText"
        />

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
        <input
          ref="fileInput"
          type="file"
          accept="image/*"
          class="file"
          @change="onFileChange"
        />
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
            <div
              v-for="s in sessions"
              :key="s.id"
              class="session"
              :class="{ on: s.id === currentSessionId }"
              @click="loadSession(s.id)"
            >
              <div class="session-top">
                <div class="session-title">
                  {{ modeLabel(s.mode) }} · {{ s.title || '未命名会话' }}
                </div>
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
    </div>
  </PageShell>
</template>

<script setup>
import { computed, nextTick, onMounted, onBeforeUnmount, ref } from "vue";
import PageShell from "../components/PageShell.vue"; 

/** ============ 配置：四类模式 ============ */
const modes = [
  { key: "common", label: "常用", ico: "💬" },
  { key: "child", label: "儿童", ico: "🧒" },
  { key: "pregnant", label: "孕妇", ico: "🤰" },
  { key: "elder", label: "老年", ico: "👴" },
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

function newSession() {
  const idx = sessions.value.length + 1;
  const s = {
    id: uid(),
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

async function callAI(kind, payload) {
  // TODO: 替换成真实四个接口调用
  // - common / child / pregnant / elder
  // payload: { text, images? }
  await new Promise(r => setTimeout(r, 700));

  const prefix = {
    common: "【常用】",
    child: "【儿童】",
    pregnant: "【孕妇】",
    elder: "【老年】",
  }[kind] || "【常用】";

  const t = payload.text?.trim() ? `我收到你的描述：${payload.text}\n\n` : "";
  const img = payload.hasImage ? "我也收到你上传的图片（已记录）。\n\n" : "";
  return `${prefix}${t}${img}请补充：症状开始时间、严重程度、是否发热/疼痛、既往史与当前用药。\n\n若出现胸痛呼吸困难、意识异常、持续高热不退、明显出血等，请尽快就医/急诊。`;
}

async function sendText() {
  const text = input.value.trim();
  if (!text || loading.value) return;

  currentSession.value.messages.push({
    id: uid(),
    role: "user",
    type: "text",
    time: nowTime(),
    text,
  });
  input.value = "";
  touchSessionPreview();
  scrollToBottom();

  loading.value = true;
  try {
    const reply = await callAI(mode.value, { text, hasImage: false });
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
.consult-page{
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
.nav{
  background:#fff;
  border:1px solid #e7efef;
  border-radius:14px;
  padding:10px 10px;
  display:grid;
  grid-template-columns: 40px 1fr 40px;
  align-items:center;
  gap: 10px;
}
.icon-btn{
  width: 40px; height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,.08);
  background: #fff;
  cursor: pointer;
  font-size: 18px;
}
.nav-title .t1{
  font-weight: 900;
  color:#123;
  font-size: 15px;
  line-height: 1.1;
}
.nav-title .t2{
  margin-top: 3px;
  font-size: 12px;
  color:#6b7f7f;
}

/* 类别 */
.modes{
  background:#fff;
  border:1px solid #e7efef;
  border-radius:14px;
  padding:10px;
  display:grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.mode{
  border: 1px solid rgba(0,0,0,.08);
  background:#fff;
  border-radius:12px;
  padding: 8px 6px;
  cursor:pointer;
  display:grid;
  justify-items:center;
  gap: 2px;
}
.mode.on{
  border-color: rgba(23,162,162,.45);
  background: rgba(23,162,162,.10);
}
.mode .ico{ font-size: 16px; }
.mode .txt{ font-size: 11px; color:#2a3c3c; font-weight: 800; }

/* 提示 */
.hint{
  background:#fff;
  border:1px solid #e7efef;
  border-radius:14px;
  padding: 10px 12px;
  display:flex;
  gap: 8px;
  align-items:flex-start;
}
.dot{
  width: 8px; height: 8px;
  border-radius: 99px;
  background:#17a2a2;
  margin-top: 4px;
}
.hint-text{
  font-size: 12px;
  color:#4f6464;
  line-height: 1.35;
}

/* 消息区 */
.msgs{
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 2px;
}
.row{
  display:flex;
  margin: 8px 0;
}
.row.user{ justify-content: flex-end; }
.row.ai{ justify-content: flex-start; }
.bubble{
  max-width: 82%;
  border-radius: 14px;
  padding: 10px;
  border: 1px solid rgba(0,0,0,.06);
  background: #fff;
}
.row.user .bubble{
  background: rgba(23,162,162,.10);
  border-color: rgba(23,162,162,.20);
}
.meta{
  display:flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 11px;
  color:#6b7f7f;
  margin-bottom: 6px;
}
.who{ font-weight: 900; color:#2a3c3c; }
.text{
  font-size: 13px;
  color:#123;
  white-space: pre-wrap;
}
.img-wrap img{
  width: 100%;
  border-radius: 12px;
  display:block;
  border: 1px solid rgba(0,0,0,.06);
}
.img-caption{
  margin-top: 8px;
  font-size: 12px;
  color:#2a3c3c;
  white-space: pre-wrap;
}

/* 输入区 */
.inputbar{
  position: relative;
  background:#fff;
  border:1px solid #e7efef;
  border-radius:14px;
  padding:10px;
  display:grid;
  grid-template-columns: 40px 1fr 74px;
  gap: 10px;
  align-items:end;
}
.plus{
  width: 40px; height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,.08);
  background:#fff;
  font-size: 18px;
  cursor: pointer;
}
.input{
  width: 100%;
  resize: none;
  box-sizing: border-box;
  border: 1px solid #e7efef;
  border-radius: 12px;
  padding: 10px;
  font-size: 13px;
  outline: none;
}
.input:focus{ border-color: rgba(23,162,162,.55); }
.send{
  height: 40px;
  border-radius: 12px;
  border: 1px solid #17a2a2;
  background:#17a2a2;
  color:#fff;
  font-weight: 900;
  cursor:pointer;
}
.send:disabled{ opacity:.55; cursor:not-allowed; }

/* + 菜单 */
.plus-menu{
  position: absolute;
  left: 10px;
  bottom: 58px;
  width: 180px;
  background:#fff;
  border:1px solid rgba(0,0,0,.10);
  border-radius: 14px;
  box-shadow: 0 12px 30px rgba(0,0,0,.12);
  overflow: hidden;
  z-index: 20;
}
.menu-item{
  width: 100%;
  text-align: left;
  padding: 12px 12px;
  border: none;
  background: #fff;
  cursor: pointer;
  font-size: 13px;
}
.menu-item:hover{
  background: rgba(23,162,162,.08);
}
.file{ display:none; }

/* tabbar 安全区（不改 PageShell） */
.safe-bottom{ height: 72px; }

/* 历史弹层 */
.mask{
  position: absolute;
  left: 0; top: 0; right: 0; bottom: 64px; /* 不盖住 tabbar */
  background: rgba(0,0,0,.35);
  display: grid;
  place-items: center;
  z-index: 60;
}
.sheet{
  width: 92%;
  max-height: 84%;
  background:#fff;
  border-radius: 16px;
  border: 1px solid rgba(0,0,0,.10);
  overflow: hidden;
  display: grid;
  grid-template-rows: auto 1fr auto;
}
.sheet-head{
  padding: 12px;
  border-bottom: 1px solid rgba(0,0,0,.06);
  display:flex;
  align-items:center;
  justify-content: space-between;
  gap: 10px;
}
.sheet-title{
  font-size: 14px;
  font-weight: 900;
  color:#123;
}
.sheet-actions{ display:flex; gap: 8px; }
.btn{
  border: 1px solid rgba(0,0,0,.10);
  background:#fff;
  border-radius: 12px;
  padding: 8px 10px;
  font-size: 12px;
  cursor: pointer;
}
.btn.ghost{
  background: rgba(23,162,162,.08);
  border-color: rgba(23,162,162,.25);
}
.btn.danger{
  border-color: rgba(226,59,59,.35);
  color: #e23b3b;
}
.sheet-list{
  padding: 10px 12px;
  overflow-y: auto;
  overflow-x: hidden;
  display: grid;
  gap: 10px;
}
.session{
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 14px;
  padding: 10px;
  cursor: pointer;
}
.session.on{
  border-color: rgba(23,162,162,.45);
  background: rgba(23,162,162,.08);
}
.session-top{
  display:flex;
  justify-content: space-between;
  gap: 10px;
  align-items: baseline;
}
.session-title{
  font-weight: 900;
  color:#123;
  font-size: 13px;
}
.session-time{
  font-size: 11px;
  color:#6b7f7f;
  white-space: nowrap;
}
.session-sub{
  margin-top: 6px;
  font-size: 12px;
  color:#4f6464;
}
.sheet-foot{
  padding: 10px 12px;
  border-top: 1px solid rgba(0,0,0,.06);
  display:flex;
  justify-content: flex-end;
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