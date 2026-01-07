<template>
  <PageShell tab="advice">
    <div class="page">
      <div class="head">
        <div class="title">个性化建议与任务</div>
        <div class="sub">点击条目进入详情页</div>

        <!-- 成员切换 -->
        <div class="members">
          <button
            v-for="m in members"
            :key="m.id"
            class="chip"
            :class="{ on: m.id === activeMemberId }"
            @click="activeMemberId = m.id"
          >
            {{ m.relation || "成员" }}·{{ m.name }}
          </button>
        </div>
      </div>

      <!-- 建议列表 -->
      <div class="block">
        <div class="bt">建议</div>
        <div
          v-for="it in adviceList"
          :key="it.id"
          class="row card"
          @click="openAdvice(it.id)"
        >
          <div class="r-title">{{ it.title }}</div>
          <div class="r-sub">{{ it.reason }}</div>
        </div>
        <div v-if="adviceList.length === 0" class="empty">暂无建议</div>
      </div>

      <!-- 任务列表 -->
      <div class="block">
        <div class="bt">任务</div>
        <div
          v-for="it in taskList"
          :key="it.id"
          class="row task"
          @click="openTask(it.id)"
        >
          <div class="r-title">{{ it.title }}</div>
          <div class="r-sub">{{ it.freq }} · {{ it.due || "长期" }}</div>
        </div>
        <div v-if="taskList.length === 0" class="empty">暂无任务</div>
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
import { apiGet } from "../api/http";

const LS_MEMBER_KEY = "active_member_id";

const router = useRouter();

const members = ref([]);
const activeMemberId = ref(null);

const adviceList = ref([]);
const taskList = ref([]);

const loading = ref(false);
const errorMsg = ref("");

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

function openAdvice(id) {
  router.push(`/advice/${id}`);
}
function openTask(id) {
  router.push(`/task/${id}`);
}
</script>

<style scoped>
.page{ padding: 12px; box-sizing: border-box; }
.head{
  background: linear-gradient(180deg, #d7f3f4 0%, #f7fbfb 70%);
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 12px;
}
.title{ font-size: 15px; font-weight: 900; color:#123; }
.sub{ margin-top: 6px; font-size: 12px; color:#6b7f7f; }

.members{
  margin-top: 10px;
  display:flex; gap:8px;
  overflow-x:auto;
  padding-bottom: 2px;
}
.chip{
  border: 1px solid rgba(0,0,0,.10);
  background: rgba(255,255,255,.85);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  cursor:pointer;
  white-space: nowrap;
}
.chip.on{ border-color:#17a2a2; color:#0b6b6b; font-weight: 900; }

.block{ margin-top: 12px; }
.bt{ font-weight: 900; color:#123; margin: 6px 0 8px; }

.row{
  background:#fff;
  border:1px solid #e7efef;
  border-radius: 14px;
  padding: 10px 12px;
  cursor:pointer;
  margin-bottom: 10px;
}
.r-title{ font-weight: 900; color:#123; font-size: 13px; }
.r-sub{ margin-top: 6px; font-size: 12px; color:#607575; line-height: 1.4; }

.empty{ font-size: 12px; color:#6b7f7f; padding: 6px 0; text-align:center; }
.safe-bottom{ height: 80px; }
</style>
