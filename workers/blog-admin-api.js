/**
 * Blog 管理 API（sayayosui.site 配下・Mac 不要）
 * Route: /<ADMIN_PATH>/api/*
 */

const PAGES_BRANCH = "gh-pages";
const SESSION_COOKIE = "diary_admin_session";
const SESSION_TTL = 60 * 60 * 12;
/** Cloudflare Workers Web Crypto は PBKDF2 を最大 100000 回まで */
const PBKDF2_ITERATIONS = 100000;
const ALLOWED_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

export default {
  async fetch(request, env) {
    const adminPath = (env.ADMIN_PATH || "blog-mgt-bf8fa662").replace(/^\/|\/$/g, "");
    const url = new URL(request.url);
    const apiPrefix = `/${adminPath}/api`;
    if (!url.pathname.startsWith(apiPrefix)) {
      return new Response("Not Found", { status: 404 });
    }
    const sub = url.pathname.slice(apiPrefix.length).replace(/^\//, "");

    try {
      if (sub === "session" && request.method === "GET") {
        return json({
          ok: true,
          authenticated: await isAuthenticated(request, env),
          setupRequired: !env.ADMIN_PASSWORD_HASH || !env.SESSION_SECRET,
        });
      }
      if (sub === "login" && request.method === "POST") {
        return handleLogin(request, env, adminPath);
      }
      if (sub === "logout" && request.method === "POST") {
        return json({ ok: true }, 200, clearSessionCookie(adminPath));
      }
      if (sub === "posts" && request.method === "GET") {
        if (!(await isAuthenticated(request, env))) {
          return json({ ok: false, error: "ログインが必要です" }, 401);
        }
        const data = await loadDiary(env);
        const posts = sortPostsByDate(data.posts || []);
        return json({ ok: true, posts });
      }
      if (sub === "posts" && request.method === "POST") {
        return handleCreatePost(request, env);
      }
      if (sub.startsWith("posts/") && request.method === "DELETE") {
        return handleDeletePost(request, sub.split("/")[1], env);
      }
      return json({ ok: false, error: "Not Found" }, 404);
    } catch (err) {
      return json({ ok: false, error: String(err.message || err) }, 500);
    }
  },
};

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...extraHeaders,
    },
  });
}

function sessionCookie(token, adminPath, maxAge = SESSION_TTL) {
  return `${SESSION_COOKIE}=${token}; Path=/${adminPath}/; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`;
}

function clearSessionCookie(adminPath) {
  return { "Set-Cookie": sessionCookie("", adminPath, 0) };
}

function getCookie(request, name) {
  const raw = request.headers.get("Cookie") || "";
  for (const part of raw.split(";")) {
    const [k, ...rest] = part.trim().split("=");
    if (k === name) return rest.join("=");
  }
  return null;
}

function bytesToHex(bytes) {
  return [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function verifyPassword(password, stored) {
  const parts = String(stored).split("$");
  if (parts.length !== 3 || parts[0] !== "pbkdf2_sha256") return false;
  const salt = parts[1];
  const expected = parts[2];
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  );
  const bits = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt: enc.encode(salt),
      iterations: PBKDF2_ITERATIONS,
      hash: "SHA-256",
    },
    keyMaterial,
    256
  );
  return bytesToHex(bits) === expected;
}

async function signSession(secret, payload) {
  const enc = new TextEncoder();
  const sig = await crypto.subtle.sign("HMAC", await importHmacKey(secret), enc.encode(payload));
  const sigB64 = base64UrlEncode(new Uint8Array(sig));
  const raw = `${payload}.${sigB64}`;
  return base64UrlEncode(enc.encode(raw));
}

async function verifySession(secret, token) {
  try {
    const raw = new TextDecoder().decode(base64UrlDecode(token));
    const idx = raw.lastIndexOf(".");
    if (idx < 0) return false;
    const payload = raw.slice(0, idx);
    const sigB64 = raw.slice(idx + 1);
    const enc = new TextEncoder();
    const expected = await crypto.subtle.sign("HMAC", await importHmacKey(secret), enc.encode(payload));
    const given = base64UrlDecode(sigB64);
    if (expected.byteLength !== given.byteLength) return false;
    const ea = new Uint8Array(expected);
    const ga = new Uint8Array(given);
    let diff = 0;
    for (let i = 0; i < ea.length; i++) diff |= ea[i] ^ ga[i];
    if (diff !== 0) return false;
    const [user, expStr] = payload.split("|");
    if (user !== "admin") return false;
    return parseInt(expStr, 10) > Math.floor(Date.now() / 1000);
  } catch (_err) {
    return false;
  }
}

function base64UrlEncode(bytes) {
  let binary = "";
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  for (let i = 0; i < arr.length; i++) binary += String.fromCharCode(arr[i]);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlDecode(str) {
  const padded = str.replace(/-/g, "+").replace(/_/g, "/");
  const pad = padded + "==".slice(0, (4 - (padded.length % 4)) % 4);
  const binary = atob(pad);
  const out = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) out[i] = binary.charCodeAt(i);
  return out;
}

/** GitHub Contents API の base64 を UTF-8 文字列へ（atob だけだと日本語が化ける） */
function base64ToUtf8(b64) {
  const binary = atob(String(b64).replace(/\n/g, ""));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new TextDecoder("utf-8").decode(bytes);
}

async function readFormField(field) {
  if (field == null) return "";
  if (typeof field === "string") return field;
  if (typeof field.text === "function") return (await field.text()).trim();
  if (typeof field.arrayBuffer === "function") {
    return new TextDecoder("utf-8").decode(new Uint8Array(await field.arrayBuffer())).trim();
  }
  return String(field).trim();
}

async function importHmacKey(secret) {
  const enc = new TextEncoder();
  return crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
}

function timingSafeEqual(a, b) {
  const aa = new Uint8Array(a);
  const bb = new Uint8Array(b);
  if (aa.length !== bb.length) return false;
  let out = 0;
  for (let i = 0; i < aa.length; i++) out |= aa[i] ^ bb[i];
  return out === 0;
}

async function makeSession(secret) {
  const exp = Math.floor(Date.now() / 1000) + SESSION_TTL;
  return signSession(secret, `admin|${exp}`);
}

async function isAuthenticated(request, env) {
  const secret = env.SESSION_SECRET || "";
  const token = getCookie(request, SESSION_COOKIE);
  if (!secret || !token) return false;
  return verifySession(secret, token);
}

async function handleLogin(request, env, adminPath) {
  if (!env.ADMIN_PASSWORD_HASH || !env.SESSION_SECRET) {
    return json({ ok: false, error: "サーバー設定が未完了です" }, 500);
  }
  const body = await request.json();
  const password = String(body.password || "");
  if (!(await verifyPassword(password, env.ADMIN_PASSWORD_HASH))) {
    await sleep(800);
    return json({ ok: false, error: "パスワードが違います" }, 401);
  }
  const token = await makeSession(env.SESSION_SECRET);
  return json({ ok: true }, 200, { "Set-Cookie": sessionCookie(token, adminPath) });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function githubSettings(env) {
  const token = (env.GITHUB_TOKEN || "").trim();
  const repo = (env.GITHUB_REPO || "trokzkgnbr/sayaka-site").trim();
  const branch = (env.GITHUB_BRANCH || "main").trim() || "main";
  if (!token) throw new Error("GITHUB_TOKEN が未設定です");
  return { token, repo, branch };
}

async function ghRequest(env, path, { method = "GET", body = null, branch = null } = {}) {
  const { token, repo, branch: defaultBranch } = githubSettings(env);
  const ref = branch || defaultBranch;
  const url = `https://api.github.com/repos/${repo}/contents/${path}?ref=${encodeURIComponent(ref)}`;
  const headers = {
    Accept: "application/vnd.github+json",
    Authorization: `Bearer ${token}`,
    "User-Agent": "sayaka-blog-admin-worker",
  };
  const init = { method, headers };
  if (body) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }
  const res = await fetch(method === "GET" ? url : `https://api.github.com/repos/${repo}/contents/${path}`, init);
  if (res.status === 404) return null;
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub API ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function getFileMeta(env, path, branch = null) {
  return ghRequest(env, path, { method: "GET", branch });
}

async function loadDiary(env) {
  const meta = await getFileMeta(env, "data/diary.json");
  if (!meta || !meta.content) return { posts: [] };
  const raw = base64ToUtf8(meta.content);
  const data = JSON.parse(raw);
  return { posts: Array.isArray(data.posts) ? data.posts : [] };
}

async function putFile(env, path, bytes, message, sha, branch = null) {
  const { repo, branch: defaultBranch } = githubSettings(env);
  const targetBranch = branch || defaultBranch;
  const payload = {
    message,
    content: bytesToBase64(bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes)),
    branch: targetBranch,
  };
  if (sha) payload.sha = sha;
  const res = await fetch(`https://api.github.com/repos/${repo}/contents/${path}`, {
    method: "PUT",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "sayaka-blog-admin-worker",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`GitHub PUT ${path}: ${await res.text()}`);
}

function bytesToBase64(bytes) {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

async function deleteFile(env, path, sha, message, branch = null) {
  const { repo, branch: defaultBranch } = githubSettings(env);
  const targetBranch = branch || defaultBranch;
  const res = await fetch(`https://api.github.com/repos/${repo}/contents/${path}`, {
    method: "DELETE",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "sayaka-blog-admin-worker",
    },
    body: JSON.stringify({ message, sha, branch: targetBranch }),
  });
  if (!res.ok) throw new Error(`GitHub DELETE ${path}: ${await res.text()}`);
}

async function publishBranchFiles(env, diaryData, message, branch, { newImages = {}, deletedImages = [] } = {}) {
  const enc = new TextEncoder();
  const diaryJson = JSON.stringify(diaryData, null, 2) + "\n";
  const diaryMeta = await getFileMeta(env, "data/diary.json", branch);
  await putFile(env, "data/diary.json", enc.encode(diaryJson), message, diaryMeta?.sha, branch);

  for (const [rel, bytes] of Object.entries(newImages)) {
    const repoPath = rel.replace(/^\//, "");
    const meta = await getFileMeta(env, repoPath, branch);
    await putFile(env, repoPath, bytes, message, meta?.sha, branch);
  }
  for (const rel of deletedImages) {
    const repoPath = rel.replace(/^\//, "");
    const meta = await getFileMeta(env, repoPath, branch);
    if (meta?.sha) await deleteFile(env, repoPath, meta.sha, message, branch);
  }
}

async function publishDiary(env, diaryData, { newImages = {}, deletedImages = [] } = {}) {
  if (Array.isArray(diaryData.posts)) {
    diaryData.posts = sortPostsByDate(diaryData.posts);
  }
  const options = { newImages, deletedImages };
  await publishBranchFiles(env, diaryData, "Update blog posts.", githubSettings(env).branch, options);
  // 公開 Blog（GitHub Pages）は gh-pages を参照するため、こちらも同期する
  await publishBranchFiles(env, diaryData, "Sync public blog.", PAGES_BRANCH, options);
}

function sortPostsByDate(posts) {
  return [...posts].sort((a, b) => {
    const byDate = (b.date || "").localeCompare(a.date || "");
    if (byDate !== 0) return byDate;
    return (b.publishedAt || "").localeCompare(a.publishedAt || "");
  });
}

function titleFromBody(body) {
  const text = body.trim();
  if (!text) return "（無題）";
  return text.split(/\r?\n/)[0].trim() || "（無題）";
}

function normalizeDate(raw) {
  const value = String(raw || "").trim();
  if (!value) {
    const now = new Date(Date.now() + 9 * 60 * 60 * 1000);
    return now.toISOString().slice(0, 10);
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new Error("日付は YYYY-MM-DD 形式で入力してください");
  }
  return value;
}

function publishedAtFromDate(dateStr) {
  return `${dateStr}T${new Date().toISOString().slice(11, 19)}Z`;
}

async function handleCreatePost(request, env) {
  if (!(await isAuthenticated(request, env))) {
    return json({ ok: false, error: "ログインが必要です" }, 401);
  }
  const form = await request.formData();
  const bodyText = await readFormField(form.get("body"));
  if (!bodyText) return json({ ok: false, error: "本文を入力してください" }, 400);
  const dateStr = normalizeDate(await readFormField(form.get("date")));
  const image = form.get("image");
  if (!image || typeof image.arrayBuffer !== "function") {
    return json({ ok: false, error: "画像を選んでください" }, 400);
  }
  const mime = image.type || "application/octet-stream";
  if (!ALLOWED_IMAGE_TYPES.has(mime)) {
    return json({ ok: false, error: "画像は JPEG / PNG / WebP にしてください" }, 400);
  }
  const imageBytes = new Uint8Array(await image.arrayBuffer());
  const postId = `post-${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;
  const fname = `${postId.replace(/[^a-zA-Z0-9_-]/g, "")}.jpg`;
  const relImage = `images/diary/${fname}`;
  const post = {
    id: postId,
    date: dateStr,
    publishedAt: publishedAtFromDate(dateStr),
    title: titleFromBody(bodyText),
    body: bodyText,
    image: relImage,
  };
  const data = await loadDiary(env);
  data.posts = data.posts || [];
  data.posts.unshift(post);
  await publishDiary(env, data, { newImages: { [relImage]: imageBytes } });
  return json({ ok: true, post, published: true });
}

async function handleDeletePost(request, postId, env) {
  if (!(await isAuthenticated(request, env))) {
    return json({ ok: false, error: "ログインが必要です" }, 401);
  }
  const data = await loadDiary(env);
  const posts = data.posts || [];
  const target = posts.find((p) => p.id === postId);
  if (!target) return json({ ok: false, error: "投稿が見つかりません" }, 404);
  data.posts = posts.filter((p) => p.id !== postId);
  const deletedImage = target.image ? String(target.image) : "";
  await publishDiary(env, data, { deletedImages: deletedImage ? [deletedImage] : [] });
  return json({ ok: true, deleted: postId, published: true });
}
