<template>
    <PageShell tab="wiki">
        <!-- 1. 最外层滚动容器 -->
        <div class="reader-wrapper">

            <!-- 2. 背景装饰图 (Hero Header) -->
            <div class="article-hero">
                <img :src="getHeroImage(article?.category)" class="hero-img" />
                <div class="hero-overlay"></div>
                <!-- 悬浮返回 -->
                <button class="back-btn-float" @click="router.back()">‹</button>
            </div>

            <!-- 3. 文字内容区（像纸张一样覆盖在背景上） -->
            <div v-if="article" class="paper-content">
                <div class="article-meta">
                    <span class="category-tag"># {{ formatCategory(article.category) }}</span>
                    <span class="dot">·</span>
                    <span class="read-time">阅读约 1 分钟</span>
                </div>

                <h1 class="title">{{ article.title }}</h1>
                <div class="author-line">来源：{{ article.source || '官方指南' }}</div>

                <div class="article-body">
                    {{ article.content }}
                </div>

                <div class="article-footer">
                    <div class="end-mark">本文完</div>
                    <p class="disclaimer">⚠️ 声明：内容仅供健康参考，不作为临床诊断依据。</p>
                </div>
            </div>

            <div class="safe-bottom"></div>
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

const getHeroImage = (cat) => {
    const map = {
        child: "http://127.0.0.1:8000/static/child.png", // 温暖的母婴图
        pregnant: "http://127.0.0.1:8000/static/pregnant.png", // 孕期图
        elder: "http://127.0.0.1:8000/static/elder.webp", // 康养图
        common: "http://127.0.0.1:8000/static/common.jpg"  // 瑜伽/生活图
    };
    return map[cat] || "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?q=80&w=600";
};

const formatCategory = (cat) => {
    const map = { child: "育儿频道", pregnant: "母婴健康", elder: "中老年管理", common: "健康生活" };
    return map[cat] || "健康百科";
};
</script>

<style scoped>
/* 1. 核心：最外层滚动容器 */
.reader-wrapper {
    height: 100vh;
    overflow-y: auto;          /* 👈 改为 auto，更自然 */
    
    /* 💡 这里的颜色必须和 PageShell 底部颜色一致，或者设为透明 */
    background-color: #f5f9f8; 
    
    width: 100%;
    max-width: 500px;         /* 👈 锁定宽度，保持手机感 */
    margin: 0 auto;           /* 居中 */
}

/* 自定义滚动条：极简透明风格 */
.reader-wrapper::-webkit-scrollbar { width: 4px; }
.reader-wrapper::-webkit-scrollbar-thumb { background: rgba(23, 162, 162, 0.1); border-radius: 10px; }

/* 2. 顶部背景图：增加沉浸感 */
.article-hero {
    position: relative;
    width: 100%;
    height: 260px;           /* 稍微调高一点 */
    overflow: hidden;
}

.hero-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* 💡 关键：蒙层颜色必须和纸张背景色完美融合 */
.hero-overlay {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 120px;
    background: linear-gradient(to bottom, transparent, #f5f9f8); 
}

/* 3. 纸张内容区：增加“书卷”质感 */
.paper-content {
    position: relative;
    margin-top: -50px;       /* 👈 向上压住图片，形成层级 */
    padding: 35px 24px;      /* 左右给足留白 */
    
    /* 💡 渐变色：模拟纸张从上往下的受光感 */
    background: linear-gradient(0deg, #f5f9f8 0%, #dff5ef 100%);
    
    border-radius: 30px 30px 0 0; /* 顶部大圆角 */
    box-shadow: 0 -15px 35px rgba(0, 0, 0, 0.04); /* 极淡的顶部阴影 */
    min-height: 600px;       /* 保证页面有拉长感 */
}

.article-meta{
    color: #1a2a2a;
}

/* 4. 标题与正文美化 */
.title {
    font-size: 26px;        /* 标题加大 */
    font-weight: 900;
    color: #1a2a2a;
    line-height: 1.3;
    margin-bottom: 12px;
    letter-spacing: -0.5px;
}

.author-line {
    font-size: 13px;
    color: #8a9999;
    margin-bottom: 30px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.article-body {
  font-size: 17px;
  color: #34495e;          /* 深灰蓝色，比纯黑护眼 */
  line-height: 1.95;       /* 极宽的行距，阅读不累 */
  white-space: pre-wrap;
  text-align: justify;     /* 两端对齐，产生书籍排版感 */
}

/* 5. 底部装饰 */
.article-footer {
    margin-top: 20px;
}

.disclaimer {
    font-size: 12px;
    color: #aebdbd;
    padding: 16px;
    background: #fdfdfd;
    border: 1px solid #f0f7f7;
    border-radius: 12px;
    line-height: 1.6;
}

.back-btn-float {
  position: absolute;
  top: 20px; left: 20px;
  width: 38px; height: 38px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border: none;
  font-size: 26px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  cursor: pointer;
  z-index: 10;
  padding-bottom: 4px; /* 👈 微调箭头的视觉重心 */
}

.safe-bottom {
    height: 80px;
}
</style>