<template>
    <PageShell tab="wiki">
        <div class="wiki-detail">
            <!-- 1. 顶部导航栏 -->
            <div class="nav">
                <button class="back-btn" @click="router.back()">‹ 返回</button>
                <div class="nav-title">科普详情</div>
                <div class="spacer"></div>
            </div>

            <!-- 2. 文章主体内容 -->
            <div v-if="article" class="article-container">
                <div class="article-header">
                    <div class="tag">{{ article.category }}</div>
                    <h1 class="title">{{ article.title }}</h1>
                    <div class="meta">发布于 {{ formatDate(article.created_at) }}</div>
                </div>

                <!-- 正文区域 -->
                <div class="content-body">
                    {{ article.content }}
                </div>

                <div class="warn-box">
                    ⚠️ 声明：本百科内容仅供健康参考，不代表医疗诊断建议。如有不适请及时就医。
                </div>
            </div>

            <!-- 3. 加载中状态 -->
            <div v-else class="loading-state">
                <div class="spinner"></div>
                <p>正在为您调取医学文献...</p>
            </div>
        </div>
    </PageShell>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { apiGet } from '../api/http';
import PageShell from '../components/PageShell.vue';

const route = useRoute();
const router = useRouter();
const article = ref(null);

// 获取文章详情
onMounted(async () => {
    const id = route.params.id; // 从 URL 获取文章 ID
    try {
        const res = await apiGet(`/wiki/${id}`);
        article.value = res;
    } catch (e) {
        console.error("文章读取失败");
    }
});

// 格式化时间
const formatDate = (isoStr) => {
    if (!isoStr) return '';
    return new Date(isoStr).toLocaleDateString();
};
</script>

<style scoped>
.wiki-detail {
  padding: 0;             /* 清除外层边距，由内部容器控制 */
  height: 100vh;          /* 锁定为屏幕高度 */
  overflow-y: auto;       /* 👈 开启纵向滚动 */
  background: #fff;       /* 阅读底色为纯白 */
  display: flex;
  flex-direction: column;
}

.nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.back-btn {
    background: none;
    border: none;
    color: #17a2a2;
    font-weight: bold;
    cursor: pointer;
}

.nav-title {
    font-weight: bold;
    color: #333;
}

.spacer {
    width: 40px;
}

.article-header {
    margin-bottom: 24px;
}

.article-container {
  padding: 20px 24px;      /* 左右给足边距，像读书一样 */
  flex: 1;                 /* 撑开空间 */
}

.tag {
    display: inline-block;
    padding: 2px 8px;
    background: #e0f2f2;
    color: #17a2a2;
    border-radius: 4px;
    font-size: 10px;
    margin-bottom: 8px;
}

.title {
    font-size: 22px;
    font-weight: 900;
    color: #123;
    line-height: 1.3;
}

.meta {
    font-size: 12px;
    color: #99a;
    margin-top: 10px;
}

.content-body {
  font-size: 16px;
  color: #334455;
  line-height: 1.8;        /* 增加行间距，阅读不累 */
  white-space: pre-wrap;   /* 👈 关键：保留数据库里的换行符 */
  margin-top: 20px;
  text-align: justify;     /* 两端对齐，看起来更专业 */
}

.warn-box {
    margin-top: 40px;
    padding: 15px;
    background: #fdf7f7;
    border: 1px solid #fce4e4;
    border-radius: 12px;
    font-size: 12px;
    color: #e74c3c;
}

.loading-state {
    text-align: center;
    padding-top: 100px;
    color: #99a;
}

.safe-bottom {
  height: 140px;           /* 在文章最底部空出 120px */
  flex-shrink: 0;
}

/* 隐藏滚动条（让界面看起来更极简） */
.wiki-detail::-webkit-scrollbar {
  display: none;
}
</style>