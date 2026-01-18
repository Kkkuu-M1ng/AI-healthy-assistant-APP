<template>
  <PageShell tab="wiki">
    <!-- 1. 整个页面作为滚动容器 -->
    <div class="wiki-scroll-page">

      <div class="page-header">
        <h1 class="main-title">健康百科</h1>
        <p class="sub-title">来自权威指南的专业解读</p>
      </div>

      <!-- 2. 分类栏：粘性置顶 -->
      <div class="sticky-tabs">
        <div class="tabs-inner">
          <div v-for="tab in tabOptions" :key="tab.key" class="tab-pill" :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key">
            {{ tab.label }}
          </div>
        </div>
      </div>

      <!-- 3. 内容列表区 -->
      <div class="list-container">
        <div v-if="loading" class="loading-tip">正在翻阅档案...</div>

        <div v-for="art in wikiList" :key="art.id" class="article-card" @click="router.push(`/wiki/${art.id}`)">
          <div class="card-body">
            <div class="card-tag">{{ formatCategory(art.category) }}</div>
            <div class="card-h1">{{ art.title }}</div>
            <div class="card-summary">{{ art.summary }}</div>
          </div>
          <div class="card-arrow">›</div>
        </div>

        <div v-if="!loading && wikiList.length === 0" class="empty-box">
          暂时没有该分类的干货，去看看别的吧
        </div>
      </div>

      <!-- 底部安全区 -->
      <div class="safe-bottom"></div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { apiGet } from '../api/http';
import PageShell from '../components/PageShell.vue';

const router = useRouter();
const LS_WIKI_TAB = "active_wiki_tab"; // 👈 记忆钥匙

const tabOptions = [
  { key: 'all', label: '全部' },
  { key: 'child', label: '育儿' },
  { key: 'pregnant', label: '母婴' },
  { key: 'elder', label: '老年' },
  { key: 'common', label: '日常' },
];

// 1. 初始化 activeTab：先看小本子记没记
const activeTab = ref(localStorage.getItem(LS_WIKI_TAB) || 'all');
const wikiList = ref([]);
const loading = ref(false);

// 2. 核心加载函数
async function loadWikiList() {
  loading.value = true;
  try {
    // 💡 发送请求，如果分类是 all，后端就不传参数
    const url = activeTab.value === 'all' ? '/wiki' : `/wiki?category=${activeTab.value}`;
    const res = await apiGet(url);
    wikiList.value = res;
  } catch (e) {
    console.error("加载百科列表失败");
  } finally {
    loading.value = false;
  }
}

// 3. 监听 Tab 切换：变了就记在小本子上
watch(activeTab, (newTab) => {
  localStorage.setItem(LS_WIKI_TAB, newTab);
  loadWikiList();
});

onMounted(() => {
  loadWikiList();
});

const formatCategory = (cat) => {
  const map = { child: "育儿", pregnant: "母婴", elder: "康养", common: "日常" };
  return map[cat] || "其他";
};
</script>

<style scoped>
.wiki-scroll-page {
  height: 100vh;
  overflow-y: auto;
  /* 👈 核心：开启纵向滚动 */
  background-color: #f8fbfb;
  scroll-behavior: smooth;

  width: 100%;
  max-width: 450px;       /* 👈 建议设为 450px，这是最美观的手机预览宽度 */
  
  margin: 0 auto;        /* 👈 居中 */
  padding: 16px;    
}

/* 自定义滚动条 */
.wiki-scroll-page::-webkit-scrollbar {
  width: 4px;
}

.wiki-scroll-page::-webkit-scrollbar-thumb {
  background: #e0f2f2;
  border-radius: 10px;
}

.page-header {
  padding: 24px 20px 10px;
}

.main-title {
  font-size: 22px;
  font-weight: 900;
  color: #123;
}

.sub-title {
  font-size: 13px;
  color: #8a9999;
  margin-top: 4px;
}

/* 💡 粘性分类栏 */
.sticky-tabs {
  position: sticky;
  /* 👈 核心：吸顶逻辑 */
  top: 0;
  z-index: 100;
  background: rgba(248, 251, 251, 0.95);
  backdrop-filter: blur(8px);
  /* 磨砂玻璃效果，非常高级 */
  padding: 10px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
}

.tabs-inner {
  display: flex;
  gap: 12px;
  padding: 0 20px;
  overflow-x: auto;
  scrollbar-width: none;
}

.tabs-inner::-webkit-scrollbar {
  display: none;
}

.tab-pill {
  flex-shrink: 0;
  padding: 6px 16px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid #eef5f5;
  font-size: 13px;
  color: #6b7f7f;
  cursor: pointer;
  transition: all 0.3s;
}

.tab-pill.active {
  background: #17a2a2;
  color: #fff;
  border-color: #17a2a2;
  font-weight: bold;
  box-shadow: 0 4px 10px rgba(23, 162, 162, 0.2);
}

/* 列表卡片 */
.list-container {
  padding: 15px 20px;
}

.article-card {
  background: #fff;
  border-radius: 18px;
  padding: 18px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #f0f7f7;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.card-body {
  flex: 1;
  margin-right: 10px;
}

.card-tag {
  font-size: 10px;
  color: #17a2a2;
  background: #e0f2f2;
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.card-h1 {
  font-size: 15px;
  font-weight: 800;
  color: #1a2a2a;
  margin-bottom: 6px;
}

.card-summary {
  font-size: 12px;
  color: #7f8c8d;
  line-height: 1.4;
}

.card-arrow {
  font-size: 20px;
  color: #ddd;
}

.safe-bottom {
  height: 100px;
}
</style>