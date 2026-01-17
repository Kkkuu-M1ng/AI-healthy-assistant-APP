<template>
  <PageShell tab="wiki">
    <div class="wiki-page">
      <div class="head">
        <div class="title">健康百科</div>
        <div class="sub">汇聚专业医学知识，守护全家健康</div>
      </div>

      <!-- 1. 分类 Tab 切换 -->
      <div class="tabs">
        <div v-for="tab in tabOptions" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key">
          {{ tab.label }}
        </div>
      </div>

      <!-- 2. 文章列表 -->
      <div class="article-list">
        <div v-for="art in wikiList" :key="art.id" class="article-item" @click="router.push(`/wiki/${art.id}`)">
          <div class="item-left">
            <div class="item-title">{{ art.title }}</div>
            <div class="item-summary">{{ art.summary }}</div>
            <div class="item-tag">{{ formatCategory(art.category) }}</div>
          </div>
          <div class="item-icon">📄</div>
        </div>

        <!-- 缺省状态 -->
        <div v-if="wikiList.length === 0" class="empty">
          暂时没有该分类下的文章...
        </div>
      </div>

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

// 分类配置
const tabOptions = [
  { key: 'all', label: '全部' },
  { key: 'child', label: '育儿' },
  { key: 'pregnant', label: '母婴' },
  { key: 'elder', label: '老年' },
  { key: 'common', label: '日常' },
];

const activeTab = ref('all');
const wikiList = ref([]);

// 核心：获取列表
async function loadWikiList() {
  try {
    // 💡 请求接口：GET /api/wiki?category=all
    const res = await apiGet(`/wiki?category=${activeTab.value}`);
    wikiList.value = res;
  } catch (e) {
    console.error("加载列表失败");
  }
}

// 监听 Tab 切换
watch(activeTab, () => {
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
.wiki-page {
  padding: 16px;
  background: #f8fcfc;
  min-height: 100vh;
}

.head {
  margin-bottom: 20px;
}

.title {
  font-size: 20px;
  font-weight: 900;
  color: #123;
}

.sub {
  font-size: 12px;
  color: #6b7f7f;
  margin-top: 4px;
}

.tabs {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
  overflow-x: auto;
  padding-bottom: 5px;
}

.tab {
  font-size: 14px;
  color: #6b7f7f;
  white-space: nowrap;
  cursor: pointer;
  padding: 4px 0;
}

.tab.active {
  color: #17a2a2;
  font-weight: 900;
  border-bottom: 3px solid #17a2a2;
}

.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-item {
  background: #fff;
  padding: 16px;
  border-radius: 16px;
  border: 1px solid #eef5f5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.item-left {
  flex: 1;
  margin-right: 15px;
}

.item-title {
  font-size: 15px;
  font-weight: 800;
  color: #123;
  margin-bottom: 6px;
}

.item-summary {
  font-size: 11px;
  color: #7f8c8d;
  line-height: 1.4;
  margin-bottom: 8px;
}

.item-tag {
  display: inline-block;
  font-size: 10px;
  color: #17a2a2;
  background: #e0f2f2;
  padding: 2px 6px;
  border-radius: 4px;
}

.item-icon {
  font-size: 24px;
  opacity: 0.2;
}

.empty {
  text-align: center;
  color: #99a;
  margin-top: 100px;
  font-size: 12px;
}

.safe-bottom {
  height: 80px;
}
</style>