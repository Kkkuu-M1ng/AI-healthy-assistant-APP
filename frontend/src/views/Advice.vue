<template>
  <PageShell tab="advice">
    <div class="page">
      <div class="head">
        <div class="title">个性化建议与任务</div>
        <div class="sub">点击条目进入详情页</div>

        <!-- 成员切换 -->
        <div class="members">
          <button v-for="m in members" :key="m.id" class="chip" :class="{ on: m.id === activeMemberId }"
            @click="activeMemberId = m.id">
            {{ m.relation || "成员" }}·{{ m.name }}
          </button>
        </div>
      </div>

      <!-- 建议列表 -->
      <div class="block">
        <div class="bt">建议</div>
        <div v-for="it in adviceList" :key="it.id" class="row card" @click="openAdvice(it.id)">
          <div class="r-title">{{ it.title }}</div>
          <div class="r-sub">{{ it.reason }}</div>
        </div>
        
        <div v-if="adviceList.length === 0" class="empty">暂无建议</div>
      </div>

      <!-- 任务列表 -->
      <div class="block">
        <div class="bt">待办任务</div>

        <!-- 1. 渲染待办任务 -->
        <div v-for="it in activeTasks" :key="it.id" class="row task active-task" @click="openTask(it.id)">
          <div class="row-content">
            <div class="r-title">{{ it.title }}</div>
            <div class="r-sub">{{ it.freq }} · {{ it.due || "长期" }}</div>
          </div>
          <div class="del-box" @click.stop="removeItem('tasks', it.id)">🗑️</div>
        </div>
        <div v-if="activeTasks.length === 0" class="empty">暂时没有待办任务，真棒！</div>

        <!-- 2. 【核心新增】已完成任务折叠区 -->
        <div v-if="doneTasks.length > 0" class="done-section">
          <div class="done-header" @click="showDoneTasks = !showDoneTasks">
            <span>已完成任务 ({{ doneTasks.length }})</span>
            <span class="arrow" :class="{ rotated: showDoneTasks }">▼</span>
          </div>

          <!-- 折叠的内容 -->
          <div v-if="showDoneTasks" class="done-list">
            <div v-for="it in doneTasks" :key="it.id" class="row task finished-task">
              <div class="row-content">
                <div class="r-title gray">{{ it.title }}</div>
                <div class="r-sub">完成于 {{ it.updated_at || '刚刚' }}</div>
              </div>
              <div class="check-box checked">✅</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 给 tabbar 留安全区 -->
      <div class="safe-bottom"></div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import PageShell from "../components/PageShell.vue";
import { apiGet, getToken } from "../api/http";

const LS_MEMBER_KEY = "active_member_id";

const router = useRouter();

const members = ref([]);
const activeMemberId = ref(null);

const adviceList = ref([]);
const taskList = ref([]);

const loading = ref(false);
const errorMsg = ref("");

// 1. 增加控制折叠的状态
const showDoneTasks = ref(false);

// 2. 增加两个计算属性，自动过滤任务
// 待办任务：done 为 false
const activeTasks = computed(() => {
  return taskList.value.filter(t => !t.done);
});

// 已完成任务：done 为 true
const doneTasks = computed(() => {
  return taskList.value.filter(t => t.done);
});

const activeMember = computed(() => {
  return members.value.find(m => m.id === activeMemberId.value) || members.value[0] || null;
});

async function loadListsByMember() {
  if (!activeMemberId.value) {
    adviceList.value = [];
    taskList.value = [];
    return;
  }
  const mid = activeMemberId.value;
  const [advice, tasks] = await Promise.all([
    apiGet(`/advice?member_id=${mid}`),
    apiGet(`/tasks?member_id=${mid}`),
  ]);
  adviceList.value = advice;
  taskList.value = tasks;
}

async function loadMembers() {
  const res = await apiGet("/members");
  members.value = res;

  // 💡 重点：同步首页的选中状态
  const savedId = localStorage.getItem(LS_MEMBER_KEY);

  if (savedId && res.find(m => m.id == savedId)) {
    activeMemberId.value = parseInt(savedId);
  } else {
    activeMemberId.value = res[0]?.id ?? null;
  }
}

// 2. 同样的，建议页切换了成员，也要同步回小本子
watch(activeMemberId, async (newId) => {
  if (newId) {
    localStorage.setItem(LS_MEMBER_KEY, newId); // 记录同步
    loading.value = true;
    try {
      await loadListsByMember();
    } finally {
      loading.value = false;
    }
  }
});

onMounted(async () => {
  loading.value = true;
  errorMsg.value = "";
  try {
    await loadMembers();
    await loadListsByMember();
  } catch (e) {
    errorMsg.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
});

// ✅ 顶部 chip 切换成员后，自动刷新列表
watch(activeMemberId, async () => {
  loading.value = true;
  errorMsg.value = "";
  try {
    await loadListsByMember();
  } catch (e) {
    errorMsg.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
});

// 1. 跳转到建议详情
function openAdvice(id) {
  router.push(`/advice/${id}`);
}

// 2. 跳转到任务详情
function openTask(id) {
  router.push(`/task/${id}`);
}

// 3. 删除功能 (确保导入了 getToken)
async function removeItem(type, id) {
  if (!confirm(`准备删除 ${type} (ID: ${id})，确认吗？`)) return;

  // 1. 打印拼接后的完整 URL，看看对不对
  const url = `http://127.0.0.1:8000/api/${type}/${id}`;
  console.log("🌐 正在发起删除请求:", url);

  try {
    const resp = await fetch(url, {
      method: 'DELETE',
      headers: { 
        "Authorization": `Bearer ${getToken()}` 
      }
    });

    // 2. 检查状态码
    console.log("📥 后端响应状态码:", resp.status);

    if (resp.ok) {
      console.log("✅ 后端删除成功");
      await loadListsByMember(); // 重新拉取列表
      alert("删除成功！");
    } else {
      // 3. 如果不 OK，看看后端吐出了什么错误信息
      const errText = await resp.text();
      console.error("❌ 后端返回错误内容:", errText);
      alert(`删除失败 (状态码: ${resp.status})\n错误信息: ${errText}`);
    }
  } catch (e) {
    // 4. 如果是网络崩溃或代码语法错误，打印在这里
    console.error("💥 浏览器捕获到异常:", e);
    alert("删除请求发送失败，请查看 F12 控制台日志。");
  }
}

// 4. 任务打卡完成
async function handleCompleteTask(task) {
  try {
    // 调用我们之前写好的 complete 接口
    await apiPost(`/tasks/${task.id}/complete`, {});
    // 重新加载数据，看到任务“瞬移”到已完成区域
    await loadListsByMember();
  } catch (e) {
    alert("操作失败");
  }
}
</script>

<style scoped>
/* 1. 基础页面布局 */
.page {
  /* ❌ 绝对不要写 100vh */
  min-height: 100%;
  width: 100%;
  max-width: 100vw;
  margin: 0;
  display: flex;
  flex-direction: column;

  padding: 16px;
  box-sizing: border-box;
  background: linear-gradient(0deg, #f5f9f8 0%, #dff5ef 100%);
}

/* 隐藏滚动条 */
.page::-webkit-scrollbar {
  display: none;
}

/* 2. 顶部面板 */
.head {
  background: linear-gradient(180deg, #d7f3f4 0%, #f7fbfb 100%);
  border: 1px solid #e7efef;
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(23,162,162,0.05);
  width: 100%;             /* 👈 必须是 100% */
  box-sizing: border-box;  /* 👈 必须加这一行 */
}

.title { font-size: 16px; font-weight: 900; color: #123; }
.sub { margin-top: 6px; font-size: 12px; color: #6b7f7f; }

.members {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.chip {
  border: 1px solid rgba(0, 0, 0, .08);
  background: rgba(255, 255, 255, .9);
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.chip.on {
  border-color: #17a2a2;
  background: #17a2a2;
  color: #fff;
  font-weight: bold;
}

/* 3. 通用列表区块 */
.block {
  margin-top: 16px;
  flex-shrink: 0;
}

.bt {
  font-weight: 900;
  color: #123;
  margin: 10px 0 12px 4px;
  font-size: 14px;
}

/* 4. 通用卡片样式 (建议与任务通用) */
.row {
  background: #fff;
  border: 1px solid #eef5f5;
  border-radius: 14px;
  padding: 14px;
  width: 100%;
  margin-bottom: 10px;
  display: flex; /* 👈 左右布局 */
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
  cursor: pointer;
  transition: transform 0.1s;
}

.row:active { transform: scale(0.98); }

.row-content {
  flex: 1; /* 👈 文字占满剩余空间 */
  text-align: left; /* 👈 强制左对齐 */
}

.r-title { font-weight: 800; color: #123; font-size: 14px; line-height: 1.4; }
.r-sub { margin-top: 4px; font-size: 12px; color: #607575; line-height: 1.4; }

/* 5. 待办任务特有样式 */
.active-task {
  border-left: 4px solid #17a2a2; /* 绿色左边框表示待办 */
}

.del-box {
  width: 22px;
  height: 22px;
  border: 2px solid #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #ffffff;
  flex-shrink: 0;
}

/* 6. 已完成任务折叠区域 */
.done-section {
  margin-top: 10px;
}

.done-header {
  padding: 10px 14px;
  background: #eff5f5;
  border-radius: 10px;
  font-size: 12px;
  color: #5d7070;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  margin-bottom: 10px;
}

.finished-task {
  background: #fdfdfd !important;
  border: 1px solid #f0f4f4 !important;
  opacity: 0.8; /* 稍微淡一点，表示历史 */
}

.finished-task .r-title.gray {
  color: #7f8c8d; /* 深灰色，保证可读性 */
  text-decoration: line-through; /* 划线效果 */
}

.check-box.checked {
  background: #e0f2f2;
  border-color: #17a2a2;
}

.arrow {
  font-size: 10px;
  transition: transform 0.3s;
}
.arrow.rotated {
  transform: rotate(180deg);
}

/* 7. 其他辅助样式 */
.empty {
  font-size: 12px;
  color: #99a;
  padding: 30px 0;
  text-align: center;
}

.safe-bottom {
  height: 100px;
  flex-shrink: 0;
}
</style>
