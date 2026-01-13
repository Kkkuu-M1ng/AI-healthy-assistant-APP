<template>
  <PageShell tab="advice">
    <div class="page">
      <!-- 顶部栏 -->
      <div class="nav">
        <button class="back" @click="router.back()">‹</button>
        <div class="title">任务详情</div>
        <div class="spacer"></div>
      </div>

      <div div v-if="task" class="card">
        <div class="h1">{{ task.title }}</div>
        <div class="sub">ID：{{ id }} · {{ task.freq }} · {{ task.due || "长期任务" }}</div>

        <div class="panel">
          <div class="row">
            <div class="k">当前状态</div>
            <div class="v">{{ done ? "已完成" : "未完成" }}</div>
          </div>

          <button class="btn" @click="toggleDone">
            {{ done ? "取消完成" : "标记完成" }}
          </button>
        </div>

        <div class="section">
          <div class="st">执行要点</div>
          <ul class="ul">
            <li v-for="(x,i) in task.steps" :key="i">{{ x }}</li>
          </ul>
        </div>

        <div class="section">
          <div class="st">完成记录</div>
          <div v-if="logs.length" class="logs">
            <div v-for="(x,i) in logs" :key="i" class="log">{{ x }}</div>
          </div>
          <div v-else class="empty">暂无记录</div>
        </div>

        <div class="warn">
          ⚠️ 本功能为健康管理打卡，不替代医生诊断；如不适明显请及时就医。
        </div>
      </div>

      <!-- 给 tabbar 留安全区 -->
      <div style="height: 80px;"></div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import PageShell from "../components/PageShell.vue";
// 💡 引入 apiGet 和 apiPost
import { apiGet, apiPost } from "../api/http";

const route = useRoute();
const router = useRouter();

const id = computed(() => route.params.id);
const task = ref(null);
const loading = ref(true);

// 状态控制
const done = ref(false);
const logs = ref([]);

// 1. 加载真实数据
async function loadTaskDetail() {
  loading.value = true;
  try {
    const res = await apiGet(`/tasks/${id.value}`);
    task.value = {
      ...res,
      // 解析执行要点
      steps: res.detail && res.detail.length > 0 ? res.detail : ["遵照AI制定的频率执行"]
    };
    done.value = res.done;
    logs.value = res.logs || [];
  } catch (e) {
    console.error("获取任务详情失败", e);
  } finally {
    loading.value = false;
  }
}

// 2. 核心功能：标记完成
async function toggleDone() {
  if (done.value) {
    alert("该任务已完成");
    return;
  }

  if (!confirm("确认完成此项任务并同步健康画像吗？")) return;

  try {
    // 💡 调动咱们昨天写的“进化引擎”接口
    const res = await apiPost(`/tasks/${id.value}/complete`, {});
    
    if (res.ok) {
      done.value = true;
      // 模拟添加一条本地记录
      logs.value.unshift(new Date().toLocaleString());
      alert("太棒了！你的健康风险值已降低。");
    }
  } catch (e) {
    alert("打卡失败，请稍后再试");
  }
}

onMounted(() => {
  loadTaskDetail();
});
</script>

<style scoped>
.page{
  padding: 12px 12px 0;
  box-sizing: border-box;
}

.nav{
  display: grid;
  grid-template-columns: 36px 1fr 36px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.back{
  width: 36px; height: 36px;
  border: 1px solid #e7efef;
  background: #fff;
  border-radius: 12px;
  font-size: 22px;
  cursor: pointer;
}
.title{
  text-align: center;
  font-weight: 900;
  color: #123;
}
.spacer{ width: 36px; height: 36px; }

.card{
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 12px;
}
.h1{ font-size: 15px; font-weight: 900; color:#123; }
.sub{ margin-top: 6px; font-size: 12px; color:#6b7f7f; line-height: 1.4; }

.panel{
  margin-top: 12px;
  border: 1px solid #eef5f5;
  border-radius: 14px;
  padding: 12px;
  background: #fbffff;
}
.row{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom: 10px;
}
.k{ font-size: 12px; color:#6b7f7f; }
.v{ font-size: 12px; font-weight: 900; color:#123; }

.btn{
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: 10px 10px;
  cursor: pointer;
  font-weight: 900;
  background: #17a2a2;
  color: #fff;
}

.section{ margin-top: 12px; }
.st{ font-weight: 900; color:#123; margin-bottom: 6px; }
.ul{ margin:0; padding-left: 18px; font-size: 13px; color:#2a3c3c; line-height: 1.6; }

.logs{ display:grid; gap: 6px; }
.log{
  font-size: 12px;
  padding: 8px 10px;
  border: 1px solid #eef5f5;
  border-radius: 12px;
  background:#fff;
  color:#2a3c3c;
}
.empty{ font-size: 12px; color:#6b7f7f; padding: 6px 0; }

.warn{
  margin-top: 12px;
  font-size: 12px;
  color:#6b7f7f;
}
</style>
