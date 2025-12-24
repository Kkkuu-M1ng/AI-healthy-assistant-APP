<template>
  <div class="page">
    <!-- 顶部：标题 + 今日摘要 -->
    <header class="header">
      <div>
        <h1 class="title">AI 家庭健康助手</h1>
        <p class="desc">为你和家人提供个性化建议、问诊记录与健康百科</p>
      </div>
      <div class="pill">今天：{{ today }}</div>
    </header>

    <!-- 模块1：健康提醒 -->
    <section class="card">
      <div class="card-head">
        <h2 class="card-title">健康提醒</h2>
        <button class="link" @click="toast('这里未来跳转到提醒列表页')">查看全部 →</button>
      </div>

      <div class="remind-grid">
        <div class="remind-item">
          <div class="remind-icon">💧</div>
          <div>
            <div class="remind-title">喝水</div>
            <div class="remind-sub">目标：1500ml（示例）</div>
          </div>
        </div>

        <div class="remind-item">
          <div class="remind-icon">🧘</div>
          <div>
            <div class="remind-title">运动</div>
            <div class="remind-sub">散步 20 分钟（示例）</div>
          </div>
        </div>

        <div class="remind-item">
          <div class="remind-icon">💊</div>
          <div>
            <div class="remind-title">用药</div>
            <div class="remind-sub">晚饭后提醒（示例）</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 模块2：家庭成员概览 -->
    <section class="card">
      <div class="card-head">
        <h2 class="card-title">家庭成员</h2>
        <button class="link" @click="toast('这里未来跳转到家庭成员管理页')">管理成员 →</button>
      </div>

      <div class="member-grid">
        <div
          v-for="m in members"
          :key="m.id"
          class="member"
          @click="toast(`查看 ${m.name} 的个性化建议（下一步做）`)"
        >
          <div class="avatar">{{ m.avatar }}</div>
          <div class="m-right">
            <div class="m-name">{{ m.name }} <span class="m-rel">· {{ m.relation }}</span></div>
            <div class="m-tags">
              <span class="tag" v-for="t in m.tags" :key="t">{{ t }}</span>
            </div>
          </div>
        </div>

        <div class="member add" @click="toast('新增家庭成员（下一步做表单页）')">
          <div class="avatar">＋</div>
          <div class="m-right">
            <div class="m-name">新增成员</div>
            <div class="m-sub">记录身高体重、基础病、过敏史等</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 模块3：AI 问诊入口 -->
    <section class="card consult">
      <div>
        <h2 class="card-title">AI 问诊</h2>
        <p class="desc2">输入症状，AI 会追问细化，并给出建议与就医提示（仅供参考）。</p>
      </div>
      <button class="primary" @click="toast('下一步我们做问诊页 UI')">开始问诊</button>
    </section>

    <!-- 模块4：健康百科 -->
    <section class="card">
      <div class="card-head">
        <h2 class="card-title">健康百科</h2>
        <button class="link" @click="toast('这里未来跳转到百科列表页')">进入百科 →</button>
      </div>

      <div class="wiki-grid">
        <div class="wiki" v-for="w in wiki" :key="w.title" @click="toast(`打开：${w.title}`)">
          <div class="wiki-title">{{ w.title }}</div>
          <div class="wiki-sub">{{ w.desc }}</div>
        </div>
      </div>
    </section>

    <footer class="footer">
      <span>提示：本应用建议仅供参考，不能替代医生诊断；如症状严重请及时就医。</span>
    </footer>
  </div>
</template>

<script>
export default {
  name: "App",
  data() {
    const d = new Date();
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");

    return {
      today: `${yyyy}-${mm}-${dd}`,
      members: [
        { id: 1, name: "我", relation: "本人", avatar: "🙂", tags: ["重点关注", "睡眠", "饮食"] },
        { id: 2, name: "妈妈", relation: "母亲", avatar: "👩", tags: ["血压", "用药提醒"] },
        { id: 3, name: "爸爸", relation: "父亲", avatar: "👨", tags: ["血脂", "运动"] },
      ],
      wiki: [
        { title: "高血压：日常管理要点", desc: "饮食、运动、用药依从性与风险提示" },
        { title: "感冒/发热：居家处理与就医时机", desc: "常见症状、红旗症状与用药注意" },
        { title: "胃痛与消化不良", desc: "诱因、饮食建议与需就医情况" },
      ],
    };
  },
  methods: {
    toast(msg) {
      alert(msg);
    },
  },
};
</script>

<style scoped>
.page {
  max-width: 980px;
  margin: 0 auto;
  padding: 22px 16px 40px;
  font-family: Arial, sans-serif;
  color: #111;
}

.header {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 14px;
}

.title {
  margin: 0;
  font-size: 28px;
  letter-spacing: 0.2px;
}

.desc {
  margin: 8px 0 0;
  color: #666;
  line-height: 1.5;
}

.pill {
  border: 1px solid #eee;
  padding: 8px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: #444;
  white-space: nowrap;
}

.card {
  border: 1px solid #eee;
  border-radius: 14px;
  padding: 16px;
  margin: 14px 0;
  background: #fff;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.card-title {
  margin: 0;
  font-size: 18px;
}

.link {
  border: none;
  background: transparent;
  color: #444;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 8px;
}

.link:hover {
  background: #f6f6f6;
}

.remind-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.remind-item {
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  cursor: pointer;
}

.remind-item:hover {
  border-color: #e6e6e6;
  background: #fafafa;
}

.remind-icon {
  font-size: 20px;
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
}

.remind-title {
  font-weight: 600;
}

.remind-sub {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

.member-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.member {
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  cursor: pointer;
}

.member:hover {
  border-color: #e6e6e6;
  background: #fafafa;
}

.member.add {
  border-style: dashed;
}

.avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
  display: grid;
  place-items: center;
  font-size: 18px;
}

.m-right {
  min-width: 0;
}

.m-name {
  font-weight: 700;
}

.m-rel {
  font-weight: 400;
  color: #666;
}

.m-tags {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  background: #f6f6f6;
  color: #444;
}

.m-sub {
  margin-top: 6px;
  color: #666;
  font-size: 12px;
}

.consult {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.desc2 {
  margin: 8px 0 0;
  color: #666;
  line-height: 1.5;
  font-size: 13px;
}

.primary {
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #ddd;
  background: #111;
  color: #fff;
  cursor: pointer;
  white-space: nowrap;
}

.primary:hover {
  opacity: 0.92;
}

.wiki-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.wiki {
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
}

.wiki:hover {
  border-color: #e6e6e6;
  background: #fafafa;
}

.wiki-title {
  font-weight: 700;
}

.wiki-sub {
  margin-top: 6px;
  color: #666;
  font-size: 12px;
  line-height: 1.5;
}

.footer {
  margin-top: 18px;
  color: #888;
  font-size: 12px;
  text-align: center;
}
</style>
