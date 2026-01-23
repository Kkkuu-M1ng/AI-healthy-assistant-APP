<template>
  <PageShell tab="advice">
    <div class="page">
      <!-- 顶部栏 -->
      <div class="nav">
        <button class="back" @click="router.back()">‹</button>
        <div class="title">任务详情</div>
        <div class="spacer"></div>
      </div>

      <div v-if="task" class="card">
        <!-- 任务基本信息 -->
        <div class="h1">{{ task.title }}</div>

        <!-- 执行要点 -->
        <div class="section">
          <div class="streak" v-if="task.repeating">连续打卡: {{ streak }} 天</div>
        </div>

        <!-- 打卡按钮 -->
        <div class="panel">
          <div class="row">
            <div class="k">当前状态</div>
            <div class="v">{{ done ? "已完成" : doneToday ? "今日已打卡" : "未完成" }}</div>
          </div>

          <button class="btn" :class="{ done: done || doneToday }" @click="toggleDone" :disabled="done || doneToday">
            <span v-if="done && !task.repeating">今日已完成</span>
            <span v-else-if="doneToday && task.repeating">今日已打卡 ✅</span>
            <span v-else>标记完成</span>
          </button>
        </div>

        <!-- 分数变化 delta -->
        <div class="section" v-if="delta && Object.keys(delta).length">
          <div class="st">分数变化</div>
          <div class="delta">
            <div v-for="(d, tag) in delta" :key="tag" class="delta-item">
              【{{ tag }}】
              <span class="old">{{ d.old_score }}</span>
              <span class="rebound" v-if="d.rebound_score - d.old_score > 0">
                +{{ d.rebound_score - d.old_score }}
              </span>
              <span class="checkin" v-if="d.old_score - d.new_score > 0">
                -{{ d.old_score - d.new_score }}
              </span>
              → <span class="new">{{ d.new_score }}</span>
            </div>
          </div>
        </div>

        <!-- 完成记录 / 打卡日志 -->
        <div class="section">
          <div class="st">完成记录</div>

          <div v-if="logs.length" class="logs">
            <div v-for="(x, i) in displayedLogs" :key="i" class="log">{{ x }}</div>

            <!-- 折叠/展开按钮 -->
            <button v-if="logs.length > LOGS_SHOW_COUNT" class="toggle-logs-btn"
              @click="logsCollapsed = !logsCollapsed">
              {{ logsCollapsed ? `显示全部 (${logs.length})` : "折叠" }}
            </button>
          </div>
          <div v-else class="empty">暂无记录</div>
        </div>


        <div class="warn">
          ⚠️ 本功能为健康管理打卡，不替代医生诊断；如不适明显请及时就医。
        </div>

        <!-- 安全区 / 风险等级 -->
        <div class="section" v-if="task.repeating">
          <div class="st">安全区进度</div>

          <div class="safe-zone">
            <!-- 等级条 -->
            <div class="level-bar">
              <div v-for="lvl in task.safe_levels" :key="lvl.level"
                :class="['level', { active: lvl.level <= task.current_level }]" :style="{
                  background: lvl.level <= task.current_level ? `linear-gradient(90deg, #17a2a2, #4dd0d0)` : '#eef5f5',
                  color: lvl.level <= task.current_level ? '#fff' : '#666'
                }">
                {{ lvl.level }}级 ({{ lvl.min_score }}-{{ lvl.max_score }})
              </div>
            </div>

            <!-- 当前进度条 -->
            <div class="progress-bar-wrapper">
              <div class="progress-bar-bg">
                <div class="progress-bar-fill"
                  :style="{ width: progressPercent + '%', background: 'linear-gradient(90deg, #17a2a2, #4dd0d0)' }">
                </div>
              </div>
              <div class="progress-text">
                {{ streak }}/{{ task.safe_days_needed }} 天
              </div>
            </div>

            <div class="progress-info">
              当前分数：{{ task.score }} | 风险等级：{{ task.current_level }}
            </div>
          </div>
        </div>

      </div>

      <!-- 任务说明区 -->
      <div v-if="task" class="card task-rules">
        <div class="h1">任务规则说明</div>

        <div class="section">
          <ul>
            <li><strong>分数消除机制：</strong>慢性病标签对应的分数可以通过完成相关任务逐步消除，完成一次打卡会减少部分分值。</li>
            <li><strong>回弹机制：</strong>如果连续未打卡，任务对应的分数可能回升（回弹），提示健康风险。</li>
            <li><strong>连续打卡奖励：</strong>连续完成打卡可获得额外奖励分数或降低风险等级，奖励随天数递增。</li>
            <li><strong>降级机制：</strong>连续未完成任务会触发标签等级下降或分数回弹，提醒用户注意健康状况。</li>
          </ul>
        </div>

        <div class="section note">
          <small>💡 提示：以上机制仅针对慢性病标签，感冒等短期疾病不会影响长期分数。</small>
        </div>
      </div>

      <!-- 底部安全区留白 -->
      <div style="height: 80px;"></div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import PageShell from "../components/PageShell.vue";
import { apiGet, apiPost } from "../api/http";

const route = useRoute();
const router = useRouter();
const id = computed(() => route.params.id);

// ------------------ 数据状态 ------------------
const task = ref({
  safe_levels: [
    { level: 0, min_score: 0, max_score: 14 },
    { level: 1, min_score: 15, max_score: 39 },
    { level: 2, min_score: 40, max_score: 69 },
    { level: 3, min_score: 70, max_score: 100 }
  ],
  current_level: 0,
  repeating: false,
  safe_days_needed: 7,
  score: 0,
  streak: 0,
  steps: []
});

const logsCollapsed = ref(true); // 默认折叠
const LOGS_SHOW_COUNT = 3;       // 默认显示前5条
const done = ref(false);
const doneToday = ref(false);
const logs = ref([]);
const delta = ref({});
const streak = ref(0); // 安全区天数

// ------------------ 进度条 ------------------
const progressPercent = computed(() => {
  if (!task.value.repeating) return 0;
  return Math.min(100, Math.floor((streak.value / task.value.safe_days_needed) * 100));
});

const displayedLogs = computed(() => {
  if (logsCollapsed.value) {
    return logs.value.slice(0, LOGS_SHOW_COUNT);
  }
  return logs.value;
});

// ------------------ 加载任务 ------------------
async function loadTaskDetail({ keepDone = false } = {}) {
  const res = await apiGet(`/tasks/${id.value}`);

  if (keepDone) {
    const doneCache = done.value;
    const doneTodayCache = doneToday.value;
    task.value = { ...res, steps: res.detail };
    done.value = doneCache;
    doneToday.value = doneTodayCache;
  } else {
    task.value = { ...res, steps: res.detail };
    done.value = res.done;
    doneToday.value = res.doneToday;
  }

  logs.value = res.logs || [];
  streak.value = res.streak || 0;
}


// 2. 打卡逻辑
async function toggleDone() {
  if (!confirm("确认完成打卡吗？")) return;

  // 防止重复点击
  if (done.value || doneToday.value) return;

  try {
    const res = await apiPost(`/tasks/${id.value}/complete`, {});

    if (res.ok) {
      // 💡 用后端返回的最新状态更新前端
      done.value = res.done;           // 一次性任务完成状态
      doneToday.value = res.doneToday; // 今日打卡状态
      delta.value = res.delta || {};   // 分数变化
      streak.value = res.streak ?? streak.value; // 如果后端返回 streak

      alert("打卡成功！");
    } else {
      alert(res.msg || "操作失败");
    }
  } catch (e) {
    console.error(e);
    alert("网络错误");
  }
}


onMounted(() => {
  loadTaskDetail();
});
</script>

<style scoped>
.page {
  box-sizing: border-box;
  width: 100%;
  max-width: 450px;
  margin: 0 auto;
  padding: 16px;
}

.nav {
  display: grid;
  grid-template-columns: 36px 1fr 36px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.back {
  width: 36px;
  height: 36px;
  border: 2px solid #e7efef;
  background: #fff;
  border-radius: 12px;
  font-size: 22px;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
}

.title {
  text-align: center;
  font-weight: 900;
  color: #123;
}

.spacer {
  width: 36px;
  height: 36px;
}

.card {
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 12px;
}

.h1 {
  font-size: 15px;
  font-weight: 900;
  color: #123;
}

.panel {
  margin-top: 12px;
  border: 1px solid #eef5f5;
  border-radius: 14px;
  padding: 12px;
  background: #fbffff;
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.k {
  font-size: 12px;
  color: #6b7f7f;
}

.v {
  font-size: 12px;
  font-weight: 900;
  color: #123;
}

.btn {
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: 10px 10px;
  cursor: pointer;
  font-weight: 900;
  background: #17a2a2;
  color: #fff;
}

.btn.done {
  background: #c0c0c0;
}

.section {
  margin-top: 12px;
}

.toggle-logs-btn {
  margin-top: 6px;
  font-size: 12px;
  color: #17a2a2;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: 900;
}

.st {
  font-weight: 900;
  color: #123;
  margin-bottom: 6px;
}

.ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  color: #2a3c3c;
  line-height: 1.6;
}

.logs {
  display: grid;
  gap: 6px;
}

.log {
  font-size: 12px;
  padding: 8px 10px;
  border: 1px solid #eef5f5;
  border-radius: 12px;
  background: #fff;
  color: #2a3c3c;
}

.empty {
  font-size: 12px;
  color: #6b7f7f;
  padding: 6px 0;
}

.warn {
  margin-top: 12px;
  font-size: 12px;
  color: #6b7f7f;
}

.streak {
  font-size: 12px;
  color: #17a2a2;
  margin-top: 4px;
  font-weight: 900;
}

.delta {
  margin-top: 6px;
  font-size: 12px;
  color: #123;
}

.delta-item {
  display: flex;
  gap: 4px;
}

.old {
  color: #6b7f7f;
}

.rebound {
  color: green;
  font-weight: 900;
}

.checkin {
  color: red;
  font-weight: 900;
}

.new {
  font-weight: 900;
}

.safe-zone {
  margin-top: 8px;
}

.level-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
}

.level {
  flex: 1;
  text-align: center;
  font-size: 11px;
  padding: 4px 0;
  border-radius: 6px;
  transition: all 0.5s ease;
}

.level.active {
  background: #17a2a2;
  color: #fff;
  font-weight: bold;
}

.progress-bar-wrapper {
  margin-top: 4px;
}

.progress-bar-bg {
  width: 100%;
  height: 8px;
  background: #eef5f5;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  transition: width 0.5s ease, background 0.5s ease;
  border-radius: 4px;
}

.progress-text {
  font-size: 11px;
  margin-top: 2px;
  text-align: right;
  color: #123;
}

.progress-info {
  font-size: 12px;
  color: #123;
  margin-top: 4px;
}

.task-rules {
  margin-top: 16px;
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  padding: 12px 16px;
  border-radius: 8px;
}

.task-rules .h1 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.task-rules .section ul {
  padding-left: 18px;
  margin: 0;
  list-style-type: disc;
  font-size: 14px;
  color: #333;
}

.task-rules .section.note {
  margin-top: 8px;
  color: #666;
  font-size: 12px;
}
</style>
