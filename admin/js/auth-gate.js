(function () {
  var SESSION_KEY = "diary_admin_client";
  var SESSION_TTL_MS = 12 * 60 * 60 * 1000;

  function bytesToHex(bytes) {
    return Array.from(bytes)
      .map(function (b) {
        return b.toString(16).padStart(2, "0");
      })
      .join("");
  }

  function readSession() {
    try {
      var raw = sessionStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      var data = JSON.parse(raw);
      if (!data || typeof data.exp !== "number" || data.exp <= Date.now()) {
        sessionStorage.removeItem(SESSION_KEY);
        return null;
      }
      return data;
    } catch (_err) {
      return null;
    }
  }

  function writeSession() {
    sessionStorage.setItem(
      SESSION_KEY,
      JSON.stringify({ exp: Date.now() + SESSION_TTL_MS })
    );
  }

  function clientAuthenticated() {
    return !!readSession();
  }

  function clearClientSession() {
    sessionStorage.removeItem(SESSION_KEY);
  }

  async function verifyPassword(password) {
    var cfg = window.ADMIN_AUTH;
    if (!cfg || !cfg.hash) {
      throw new Error("認証設定がありません");
    }
    var parts = String(cfg.hash).split("$");
    if (parts.length !== 3 || parts[0] !== "pbkdf2_sha256") {
      throw new Error("認証設定が不正です");
    }
    var salt = parts[1];
    var expected = parts[2];
    var iterations = cfg.iterations || 600000;
    var enc = new TextEncoder();
    var keyMaterial = await crypto.subtle.importKey(
      "raw",
      enc.encode(password),
      "PBKDF2",
      false,
      ["deriveBits"]
    );
    var bits = await crypto.subtle.deriveBits(
      {
        name: "PBKDF2",
        salt: enc.encode(salt),
        iterations: iterations,
        hash: "SHA-256",
      },
      keyMaterial,
      256
    );
    return bytesToHex(new Uint8Array(bits)) === expected;
  }

  async function loginClient(password) {
    var ok = await verifyPassword(password);
    if (!ok) {
      throw new Error("パスワードが違います");
    }
    writeSession();
    return true;
  }

  async function ensureClientAuth() {
    if (clientAuthenticated()) {
      return true;
    }
    if (!/login\.html$/.test(window.location.pathname)) {
      window.location.href = "login.html";
      return false;
    }
    return false;
  }

  function staticAuthEnabled() {
    return !!(window.ADMIN_AUTH && window.ADMIN_AUTH.hash);
  }

  window.DiaryAdminAuth = {
    staticAuthEnabled: staticAuthEnabled,
    clientAuthenticated: clientAuthenticated,
    clearClientSession: clearClientSession,
    loginClient: loginClient,
    ensureClientAuth: ensureClientAuth,
  };
})();
