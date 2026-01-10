<template>
  <PageShell tab="me">
    <div class="me-page">
      <!-- 顶部：头像 + 右侧信息 -->
      <div class="hero">
        <div class="avatar">
          <img v-if="profile.avatar" :src="profile.avatar" alt="avatar" />
          <div v-else class="avatar-fallback">
            {{ (profile.nickname || "我").slice(0, 1).toUpperCase() }}
          </div>
        </div>

        <div class="hero-right">
          <div class="hero-top">
            <div class="name">{{ profile.nickname || "未命名用户" }}</div>
            <button class="btn ghost" @click="toggleEditProfile">
              {{ editingProfile ? "完成" : "编辑" }}
            </button>
          </div>

          <div class="id-row">
            <span class="id">ID: {{ profile.id }}</span>
            <button class="btn link" @click="copyText(profile.id)">复制</button>
          </div>

          <div class="meta">
            <span v-if="profile.gender" class="chip">{{ profile.gender }}</span>
            <span v-if="profile.age" class="chip">{{ profile.age }}岁</span>
            <span v-if="bmi" class="chip">BMI {{ bmi }}</span>
            <span class="chip dim">成员 {{ members.length }} 人</span>
          </div>

          <div class="progress-card">
            <div class="progress-head">
              <span class="muted">资料完整度</span>
              <b>{{ completeness }}%</b>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: completeness + '%' }"></div>
            </div>
            <div class="tip" v-if="completeness < 80">
              建议补全身高体重、慢病/过敏、用药信息，后续个性化更准确
            </div>
          </div>
        </div>
      </div>

      <!-- 中部：个人信息（展示 / 编辑） -->
      <div class="block">
        <div class="block-title">个人信息</div>

        <!-- 展示模式 -->
        <div v-if="!editingProfile" class="card">
          <div class="kv">
            <div class="k">昵称</div>
            <div class="v">{{ profile.nickname || "-" }}</div>
          </div>
          <div class="kv">
            <div class="k">性别</div>
            <div class="v">{{ profile.gender || "-" }}</div>
          </div>
          <div class="kv">
            <div class="k">年龄</div>
            <div class="v">{{ profile.age ?? "-" }}</div>
          </div>
          <div class="kv">
            <div class="k">身高/体重</div>
            <div class="v">{{ profile.height ?? "-" }}cm / {{ profile.weight ?? "-" }}kg</div>
          </div>
          <div class="kv">
            <div class="k">慢病标签</div>
            <div class="v">
              <template v-if="profile.chronicTags.length">
                <span v-for="t in profile.chronicTags" :key="t" class="chip">{{ t }}</span>
              </template>
              <span v-else class="muted">-</span>
            </div>
          </div>
          <div class="kv">
            <div class="k">过敏史</div>
            <div class="v">{{ profile.allergies || "-" }}</div>
          </div>
          <div class="kv">
            <div class="k">常用药</div>
            <div class="v">{{ profile.meds || "-" }}</div>
          </div>
        </div>

        <!-- 编辑模式（尽量短：更多字段建议你后面放“更多/展开”） -->
        <div v-else class="card">
          <div class="form-body">
            <div class="form">
              <label class="field">
                <div class="label">昵称</div>
                <input v-model.trim="profileDraft.nickname" class="input" placeholder="例如：小明" />
              </label>

              <div class="grid2">
                <label class="field">
                  <div class="label">性别</div>
                  <select v-model="profileDraft.gender" class="input">
                    <option value="">请选择</option>
                    <option value="男">男</option>
                    <option value="女">女</option>
                    <option value="其他">其他</option>
                  </select>
                </label>

                <label class="field">
                  <div class="label">年龄</div>
                  <input v-model.number="profileDraft.age" type="number" class="input" min="0" max="120" />
                </label>
              </div>

              <div class="grid2">
                <label class="field">
                  <div class="label">身高(cm)</div>
                  <input v-model.number="profileDraft.height" type="number" class="input" min="0" max="250" />
                </label>

                <label class="field">
                  <div class="label">体重(kg)</div>
                  <input v-model.number="profileDraft.weight" type="number" class="input" min="0" max="300" />
                </label>
              </div>

              <div class="field">
                <div class="label">慢病标签</div>
                <div class="chips">
                  <span v-for="t in profileDraft.chronicTags" :key="t" class="chip">
                    {{ t }}
                    <span class="x" @click="removeTag(profileDraft.chronicTags, t)">×</span>
                  </span>
                </div>
                <div class="tag-add">
                  <input v-model.trim="tagInput" class="input" placeholder="输入标签回车或点添加"
                    @keydown.enter.prevent="addProfileTag" />
                  <button class="btn" @click="addProfileTag">添加</button>
                </div>
                <div class="preset">
                  <button v-for="t in chronicPreset" :key="t" class="pill"
                    @click="quickAddTag(profileDraft.chronicTags, t)">
                    {{ t }}
                  </button>
                </div>
              </div>

              <label class="field">
                <div class="label">过敏史</div>
                <textarea v-model.trim="profileDraft.allergies" class="input" rows="2"
                  placeholder="例如：青霉素过敏"></textarea>
              </label>

              <label class="field">
                <div class="label">常用药</div>
                <textarea v-model.trim="profileDraft.meds" class="input" rows="2" placeholder="例如：氨氯地平"></textarea>
              </label>

              <div class="actions">
                <button class="btn ghost" @click="cancelEditProfile">取消</button>
                <button class="btn primary" @click="saveProfile">保存</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部：家庭成员（列表区域可滚动，整页不滚） -->
      <div class="block members-block">
        <div class="members-head">
          <div class="block-title">家庭成员</div>
          <button class="btn primary" @click="openMember('new')">+ 新增成员</button>
        </div>

        <div class="members-scroll">
          <div v-for="m in familyMembersOnly" :key="m.id" class="member-card">
            <div class="member-top">
              <div class="member-title">{{ m.relation }}｜{{ m.name }}
                <span class="sub-info">({{ m.gender || '?' }} · {{ m.age || '0' }}岁)</span>
              </div>
              <div class="member-actions">
                <button class="btn link" @click="openMember(m.id)">编辑</button>
                <button class="btn link danger" :disabled="m.id === 'self'" @click="removeMember(m.id)">删除</button>
              </div>
            </div>

            <div class="chips" v-if="m.tags && Object.keys(m.tags).length" style="margin-top:8px;">
              <!-- 注意：现在的 m.tags 是个对象，所以用 (val, key) 的写法 -->
              <span v-for="(val, key) in m.tags" :key="key" class="chip">
                {{ key }} <span class="lv-tag">L{{ val.level }}</span>
              </span>
            </div>

            <div v-if="m.notes" class="notes">{{ m.notes }}</div>
          </div>

          <div v-if="familyMembersOnly.length === 0" class="empty">
            还没有添加家庭成员，点击右上角 “新增成员”
          </div>
        </div>
      </div>

      <!-- 成员弹窗 -->
      <div v-if="memberDialog" class="mask" @click.self="closeMemberDialog">
        <div class="dialog">
          <div class="dialog-title">{{ memberDialogTitle }}</div>

          <div class="form">
            <label class="field">
              <div class="label">姓名</div>
              <input v-model.trim="memberDraft.name" class="input" placeholder="例如：妈妈" />
            </label>

            <div class="grid2">
              <label class="field">
                <div class="label">关系</div>
                <select v-model="memberDraft.relation" class="input">
                  <option v-for="r in relationPreset" :key="r" :value="r">{{ r }}</option>
                </select>
              </label>

              <label class="field">
                <div class="label">性别</div>
                <select v-model="memberDraft.gender" class="input">
                  <option value="">请选择</option>
                  <option value="男">男</option>
                  <option value="女">女</option>
                  <option value="其他">其他</option>
                </select>
              </label>
            </div>

            <label class="field">
              <div class="label">年龄</div>
              <input v-model.number="memberDraft.age" type="number" class="input" min="0" max="120" />
            </label>

            <div class="grid2">
              <label class="field">
                <div class="label">身高(cm)</div>
                <input v-model.number="memberDraft.height" type="number" class="input" />
              </label>
              <label class="field">
                <div class="label">体重(kg)</div>
                <input v-model.number="memberDraft.weight" type="number" class="input" />
              </label>
            </div>

            <div class="field">
              <div class="label">健康标签</div>
              <div class="chips">
                <span v-for="t in memberDraft.tags" :key="t" class="chip">
                  {{ t }} <span class="x" @click="removeTag(memberDraft.tags, t)">×</span>
                </span>
              </div>
              <div class="tag-add">
                <input v-model.trim="memberTagInput" class="input" placeholder="输入标签回车或点添加"
                  @keydown.enter.prevent="addMemberTag" />
                <button class="btn" @click="addMemberTag">添加</button>
              </div>
              <div class="preset">
                <button v-for="t in chronicPreset" :key="t" class="pill" @click="quickAddTag(memberDraft.tags, t)">
                  {{ t }}
                </button>
              </div>
            </div>

            <label class="field">
              <div class="label">备注</div>
              <textarea v-model.trim="memberDraft.notes" class="input" rows="2" placeholder="例如：血压偏高，需定期复查"></textarea>
            </label>

            <div class="actions">
              <button class="btn ghost" @click="closeMemberDialog">取消</button>
              <button class="btn primary" @click="saveMember">保存</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ✅ 给 PageShell 的 tabbar 留安全区（不修改 PageShell 本身） -->
      <div class="safe-bottom"></div>
    </div>
  </PageShell>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from "vue";
import PageShell from "../components/PageShell.vue";
import { apiGet, apiPost, getToken } from "../api/http";

// ====== localStorage store（写在组件内，避免你额外建文件）======
const LS_KEY = "ai_family_doc_v1";
const API_BASE = "http://127.0.0.1:8000/api";

async function apiRequest(method, path, body) {
  const resp = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${getToken()}`
    },
    body: JSON.stringify(body)
  });
  if (!resp.ok) throw new Error(`${method} 请求失败`);
  return resp.json();
}

const profile = reactive({
  id: "",          // User ID
  memberId: null,  // "本人"在成员表里的 ID (关键)
  avatar: "",
  nickname: "加载中...",
  gender: "",
  age: null,
  height: null,
  weight: null,
  chronicTags: [],
  allergies: "",
  meds: "",
});

const members = ref([]); // 改为 ref 数组，方便整体替换
const loading = ref(false);

async function initData() {
  loading.value = true;
  try {
    // A. 并发获取：账号信息 + 家庭成员列表
    const [userRes, membersRes] = await Promise.all([
      apiGet('/me'),      // 对应 me.py 的 GET /me
      apiGet('/members')  // 对应 members.py 的 GET /members
    ]);

    // B. 填充账号基础信息
    profile.id = userRes.id;
    profile.avatar = userRes.avatar_url;
    profile.nickname = userRes.nickname;

    // C. 找到“本人”的那份健康档案
    const self = membersRes.find(m => m.relation === '本人');
    if (self) {
      profile.memberId = self.id;
      profile.gender = self.gender || "";
      profile.age = self.age;
      profile.height = self.height;
      profile.weight = self.weight;
      profile.chronicTags = self.tags ? Object.keys(self.tags) : [];
      profile.allergies = self.allergies || "";
      profile.meds = self.meds || "";
    }

    // D. 填充家庭成员列表
    members.value = membersRes;

  } catch (e) {
    console.error("加载数据失败", e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  initData();
});

const bmi = computed(() => {
  const h = Number(profile.height);
  const w = Number(profile.weight);
  if (!h || !w) return "";
  const m = h / 100;
  return (w / (m * m)).toFixed(1);
});

const completeness = computed(() => {
  const items = [
    !!profile.nickname,
    !!profile.gender,
    typeof profile.age === "number" && profile.age > 0,
    typeof profile.height === "number" && profile.height > 0,
    typeof profile.weight === "number" && profile.weight > 0,
    (profile.chronicTags?.length ?? 0) > 0,
    !!profile.allergies,
    !!profile.meds,
  ];
  return Math.round((items.filter(Boolean).length / items.length) * 100);
});

// ====== 个人信息编辑 ======
const editingProfile = ref(false);
const profileDraft = reactive(clone(profile));

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function toggleEditProfile() {
  editingProfile.value = !editingProfile.value;
  if (editingProfile.value) Object.assign(profileDraft, clone(profile));
}

function cancelEditProfile() {
  editingProfile.value = false;
}

async function saveProfile() {
  try {
    const payload = {
      name: profileDraft.nickname,
      gender: profileDraft.gender,
      age: profileDraft.age,
      height: profileDraft.height,
      weight: profileDraft.weight,
      tags: profileDraft.chronicTags,
      allergies: profileDraft.allergies,
      meds: profileDraft.meds
    };

    // 调用后端的 PUT 接口更新“本人”档案
    await apiRequest('PUT', `/members/${profile.memberId}`, payload);

    // 更新本地显示
    Object.assign(profile, clone(profileDraft));
    editingProfile.value = false;
    alert("个人信息已同步至云端");
  } catch (e) {
    alert("保存失败: " + e.message);
  }
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(String(text));
  } catch {
  }
}

// ====== 标签工具 ======
const chronicPreset = ["高血压", "糖尿病", "高血脂", "痛风", "哮喘", "冠心病", "胃炎", "肥胖", "焦虑/抑郁"];
const tagInput = ref("");

const familyMembersOnly = computed(() => {
  // 过滤掉关系为“本人”的成员，只留下真正的家属
  return members.value.filter(m => m.relation !== '本人');
});

function quickAddTag(arr, t) {
  if (!t) return;
  // 确保传入的是数组，如果因为某种原因变成了对象，这里强制初始化
  if (!Array.isArray(arr)) {
    console.error("标签容器不是数组，正在初始化...");
    return;
  }
  if (!arr.includes(t)) arr.push(t);
}

function removeTag(arr, t) {
  const i = arr.indexOf(t);
  if (i >= 0) arr.splice(i, 1);
}

function addProfileTag() {
  const t = tagInput.value.trim();
  if (!t) return;
  quickAddTag(profileDraft.chronicTags, t);
  tagInput.value = "";
}

// ====== 成员管理 ======
const relationPreset = ["父亲", "母亲", "丈夫", "妻子", "孩子", "爷爷", "奶奶"];

const memberDialog = ref(false);
const memberDialogTitle = ref("新增成员");
const editingMemberId = ref("new");

const memberDraft = reactive({
  id: "",
  name: "",
  relation: "父亲",
  gender: "",
  age: null,
  tags: [],
  notes: "",
});

const memberTagInput = ref("");

function openMember(id) {
  editingMemberId.value = id;
  memberDialog.value = true;

  if (id === "new") {
    memberDialogTitle.value = "新增成员";
    // 初始化空数据
    Object.assign(memberDraft, {
      name: "", relation: "父亲", gender: "", age: null,
      height: null, weight: null, allergies: "", meds: "", tags: []
    });
  } else {
    memberDialogTitle.value = "编辑成员";
    // 从当前的 members 列表里找到对应的成员对象
    const m = members.value.find(x => x.id === id);
    if (!m) return;

    // 【核心关键】：把 m 里的所有属性克隆给 memberDraft
    // 只要 m 里面有 height/weight，memberDraft 就会跟着有
    Object.assign(memberDraft, clone(m));

    // 特殊处理标签：后端传回来的是对象 {"高血压":{...}}，
    // 但前端编辑组件需要的是数组 ["高血压"]，所以我们要转一下
    if (m.tags && !Array.isArray(m.tags)) {
      memberDraft.tags = Object.keys(m.tags);
    }
  }
  memberTagInput.value = "";
}

function closeMemberDialog() {
  memberDialog.value = false;
}

function addMemberTag() {
  const t = memberTagInput.value.trim();
  if (!t) return;
  quickAddTag(memberDraft.tags, t);
  memberTagInput.value = "";
}

async function saveMember() {
  if (!memberDraft.name.trim()) return;
  try {
    const payload = {
      name: memberDraft.name,
      relation: memberDraft.relation,
      gender: memberDraft.gender,
      age: memberDraft.age,
      height: memberDraft.height,
      weight: memberDraft.weight,
      tags: memberDraft.tags,
      notes: memberDraft.notes 
    };

    if (editingMemberId.value === "new") {
      const res = await apiPost('/members', payload);
      members.value.unshift(res);
    } else {
      await apiRequest('PUT', `/members/${editingMemberId.value}`, payload);
      const idx = members.value.findIndex(x => x.id === editingMemberId.value);
      if (idx >= 0) members.value[idx] = clone(memberDraft);
    }

    await initData(); 

    memberDialog.value = false;
  } catch (e) {
    alert("操作失败");
  }
}

async function removeMember(id) {
  // 1. 弹窗确认，防止误点
  if (!confirm("确定要删除这位家庭成员吗？")) return;

  try {
    // 2. 发起请求
    const resp = await fetch(`http://127.0.0.1:8000/api/members/${id}`, {
      method: 'DELETE',
      headers: {
        "Authorization": `Bearer ${getToken()}`
      }
    });

    // 3. 处理结果
    if (resp.ok) {
      // 成功了：直接从当前列表里把这行数据滤掉，界面立刻就变了
      members.value = members.value.filter(m => m.id !== id);
      console.log("删除成功");
    } else {
      // 失败了（比如点到了本人）：弹出后端给的错误提示
      const err = await resp.json();
      alert(err.detail || "删除操作失败");
    }
  } catch (e) {
    alert("网络开小差了，请稍后再试");
  }
}
</script>

<style scoped>
/* ✅ 不改 PageShell：我在页面内部做安全区与布局控制 */
.me-page {
  height: 100%;
  box-sizing: border-box;
  padding: 14px 0 0;
  overflow: hidden;
  /* 整页不滚动 */
  overflow-x: hidden;
  /* ✅ 禁止左右滑动 */
  display: grid;
  grid-template-rows: auto auto 1fr;
  gap: 12px;
}

/* 顶部 */
.hero {
  padding: 14px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(23, 162, 162, .16), rgba(16, 185, 129, .10));
  border: 1px solid rgba(0, 0, 0, .05);
  display: grid;
  grid-template-columns: 76px 1fr;
  gap: 12px;
  margin-left: 8px;
  margin-right: 8px;
}

.avatar {
  width: 76px;
  height: 76px;
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, .85);
  border: 1px solid rgba(0, 0, 0, .06);
  display: grid;
  place-items: center;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  font-size: 28px;
  font-weight: 900;
  color: #0f3d3d;
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.name {
  font-size: 18px;
  font-weight: 900;
  color: #0f1f1f;
}

.id-row {
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #506363;
}

.meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.progress-card {
  margin-top: 10px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, .65);
  border: 1px solid rgba(0, 0, 0, .04);
}

.progress-head {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #1e2d2d;
  margin-bottom: 6px;
}

.progress-bar {
  height: 10px;
  border-radius: 999px;
  background: rgba(0, 0, 0, .08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: #17a2a2;
}

.tip {
  margin-top: 6px;
  font-size: 12px;
  color: #4f6464;
}

/* 区块 */
.block {
  margin-left: 8px;
  margin-right: 8px;
}

.block-title {
  margin: 4px 0 10px;
  font-size: 14px;
  font-weight: 900;
  color: #123;
  margin-left: 20px;
}

.card {
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  max-height: 500px;
  /* 设置一个固定最大高度，你可以根据需要调整 */
  padding: 0 !important;
  /* 清除原有 padding，由内部容器控制 */
}

/* kv展示 */
.kv {
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px dashed rgba(0, 0, 0, .06);
}

.kv:last-child {
  border-bottom: none;
}

.k {
  font-size: 12px;
  color: #6b7f7f;
}

.v {
  font-size: 13px;
  color: #123;
}

/* 表单 */
.form-body {
  flex: 1;
  overflow-y: auto;
  /* 开启垂直滚动 */
  padding: 15px;
  /* 把内边距还给滚动区 */
}

.form {
  display: grid;
  gap: 10px;
}

.field .label {
  font-size: 12px;
  color: #6b7f7f;
  margin-bottom: 6px;
}

.input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #e7efef;
  border-radius: 12px;
  padding: 10px 10px;
  font-size: 13px;
  outline: none;
  background: #fff;
  resize: none;
  overflow-y: auto;
}

.input:focus {
  border-color: rgba(23, 162, 162, .6);
}

.grid2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 4px;
}

/* 成员区：占剩余空间 + 内部滚动 */
.members-block {
  min-height: 0;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 10px;
}

.members-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.members-scroll {
  min-height: 0;
  overflow-y: auto;
  /* 只滚成员列表 */
  overflow-x: hidden;
  /* ✅ 禁止左右滑 */
  display: grid;
  gap: 10px;
  padding-right: 2px;
  /* 防止滚动条遮一点点 */
}

.member-card {
  background: #fff;
  border: 1px solid #e7efef;
  border-radius: 14px;
  padding: 12px;
}

.member-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.member-title {
  font-weight: 900;
  color: #123;
  font-size: 14px;
}

/* 姓名旁边的副信息 */
.sub-info {
  font-size: 12px;
  color: #8a9999;
  font-weight: normal;
  margin-left: 6px;
}

/* 标签里的等级文字 */
.lv-tag {
  font-size: 10px;
  background: #17a2a2;
  color: #fff;
  padding: 0 4px;
  border-radius: 4px;
  margin-left: 4px;
  font-weight: bold;
}

.notes {
  margin-top: 8px;
  font-size: 12px;
  color: #2a3c3c;
}

/* Chip */
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 12px;
  border: 1px solid rgba(0, 0, 0, .08);
  background: rgba(255, 255, 255, .65);
  color: #123;
}

.chip.dim {
  color: #516666;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.x {
  cursor: pointer;
  opacity: .7;
  font-weight: 900;
}

.x:hover {
  opacity: 1;
}

/* Tag 添加 */
.tag-add {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  margin-top: 8px;
}

.preset {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.pill {
  border: 1px dashed rgba(0, 0, 0, .18);
  background: transparent;
  color: #275;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}

.pill:hover {
  border-style: solid;
}

/* 按钮 */
.btn {
  border: 1px solid rgba(0, 0, 0, .08);
  background: #fff;
  border-radius: 12px;
  padding: 8px 10px;
  font-size: 12px;
  cursor: pointer;
}

.btn.primary {
  background: #17a2a2;
  border-color: #17a2a2;
  color: #fff;
  font-weight: 800;
}

.btn.ghost {
  background: rgba(255, 255, 255, .65);
}

.btn.link {
  border: none;
  background: transparent;
  padding: 6px 6px;
  color: #17a2a2;
  font-weight: 800;
}

.btn.link.danger {
  color: #e23b3b;
}

.btn:disabled {
  opacity: .45;
  cursor: not-allowed;
}

.muted {
  color: #6b7f7f;
}

/* 弹窗 */
.mask {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  bottom: 64px;
  /* 不盖住 tabbar */
  background: rgba(0, 0, 0, .35);
  display: grid;
  place-items: center;
  z-index: 50;
}

.dialog {
  width: 92%;
  max-height: 86%;
  overflow: auto;
  background: #fff;
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, .08);
  padding: 14px;
  box-sizing: border-box;
}

.dialog-title {
  font-size: 14px;
  font-weight: 900;
  color: #123;
  margin-bottom: 10px;
}

.empty {
  text-align: center;
  color: #6b7f7f;
  font-size: 12px;
  padding: 14px 0;
}

/* ✅ 底部安全区：避免内容被 tabbar 压住（不改 PageShell） */
.safe-bottom {
  height: 72px;
}
</style>
