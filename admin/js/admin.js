(function () {
  function qs(sel) {
    return document.querySelector(sel);
  }

  function showMessage(el, text, type) {
    if (!el) return;
    if (!text) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = text;
    el.className = "admin-message admin-message--" + (type || "error");
  }

  async function api(path, options) {
    const res = await fetch(path, Object.assign({ credentials: "same-origin" }, options || {}));
    let data = null;
    try {
      data = await res.json();
    } catch (_err) {
      data = null;
    }
    if (!res.ok) {
      throw new Error((data && data.error) || "通信に失敗しました");
    }
    return data;
  }

  async function ensureAuth() {
    try {
      const data = await api("api/session");
      if (data.setupRequired) {
        window.location.href = "setup.html";
        return false;
      }
      if (data.authenticated) {
        return true;
      }
      window.location.href = "login.html";
      return false;
    } catch (_err) {
      if (window.DiaryAdminAuth && window.DiaryAdminAuth.staticAuthEnabled()) {
        return window.DiaryAdminAuth.ensureClientAuth();
      }
      window.location.href = "login.html";
      return false;
    }
  }

  async function login(password) {
    try {
      await api("api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: password }),
      });
      return true;
    } catch (err) {
      if (window.DiaryAdminAuth && window.DiaryAdminAuth.staticAuthEnabled()) {
        await window.DiaryAdminAuth.loginClient(password);
        return true;
      }
      throw err;
    }
  }

  async function logout() {
    try {
      await api("api/logout", { method: "POST" });
    } catch (_err) {
      /* static mode */
    }
    if (window.DiaryAdminAuth) {
      window.DiaryAdminAuth.clearClientSession();
    }
    window.location.href = "login.html";
  }

  window.DiaryAdmin = {
    api: api,
    showMessage: showMessage,
    ensureAuth: ensureAuth,
    login: login,
    logout: logout,
    qs: qs,
  };
})();
