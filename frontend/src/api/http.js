// src/api/http.js 封装 fetch、自动带 Authorization、没 token 时调用 /api/auth/dev 先拿 token
const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api";

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
