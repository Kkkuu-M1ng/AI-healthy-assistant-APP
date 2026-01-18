// src/api/http.js 封装 fetch、自动带 Authorization、没 token 时调用 /api/auth/dev 先拿 token
// 💡 智能识别当前环境
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// 1. 根据环境自动选择后端地址
// 以后重启 cpolar，你只需要改下面这一行网址就行
const PUBLIC_BACKEND = "http://3ab9df0f.r15.cpolar.top"; 
const LOCAL_BACKEND  = "http://127.0.0.1:8000";

export const BACKEND_URL = isLocal ? LOCAL_BACKEND : PUBLIC_BACKEND;
export const API_BASE = `${BACKEND_URL}/api`;

console.log(`📡 当前 App 正在连接后端：${BACKEND_URL}`);

const TOKEN_KEY = "ai_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}
export function setToken(t) {
  localStorage.setItem(TOKEN_KEY, t);
}

async function devLoginIfNeeded() {
  if (getToken()) return;

  const resp = await fetch(`${API_BASE}/auth/dev`, { method: "POST" });
  if (!resp.ok) throw new Error(`dev 登录失败：${resp.status}`);

  const data = await resp.json();

  // 兼容两种返回：字符串 token 或 {access_token/token: "..."}
  const token =
    typeof data === "string"
      ? data
      : data.access_token || data.token || data.data || "";

  if (!token) throw new Error("dev 登录接口未返回 token");
  setToken(token);
}

export async function apiGet(path) {
  await devLoginIfNeeded();

  const resp = await fetch(`${API_BASE}${path}`, {
    headers: {
      Authorization: `Bearer ${getToken()}`,
    },
  });

  if (!resp.ok) {
    // 👇👇👇 新增：自动修复逻辑 👇👇👇
    if (resp.status === 401) {
      console.warn("检测到 Token 失效，正在自动清理并重启...");
      localStorage.removeItem("ai_token"); // 删掉僵尸 Token
      location.reload(); // 刷新页面，触发 devLoginIfNeeded 重新领钥匙
      return;
    }
    // 👆👆👆👆👆👆👆👆👆👆👆👆

    const text = await resp.text().catch(() => "");
    throw new Error(`GET ${path} 失败：${resp.status} ${text}`);
  }
  return resp.json();
}

export async function apiPost(path, body) {
  await devLoginIfNeeded();

  const resp = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    // 👇👇👇 新增：自动修复逻辑 👇👇👇
    if (resp.status === 401) {
      console.warn("检测到 Token 失效，正在自动清理并重启...");
      localStorage.removeItem("ai_token"); // 删掉僵尸 Token
      location.reload(); // 刷新页面，触发 devLoginIfNeeded 重新领钥匙
      return;
    }
    // 👆👆👆👆👆👆👆👆👆👆👆👆

    const text = await resp.text().catch(() => "");
    throw new Error(`GET ${path} 失败：${resp.status} ${text}`);
  }
  return resp.json();
}
