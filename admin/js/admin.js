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
    const data = await api("/admin/api/session");
    if (!data.authenticated) {
      window.location.href = "/admin/login.html";
      return false;
    }
    return true;
  }

  async function logout() {
    await api("/admin/api/logout", { method: "POST" });
    window.location.href = "/admin/login.html";
  }

  window.DiaryAdmin = {
    api: api,
    showMessage: showMessage,
    ensureAuth: ensureAuth,
    logout: logout,
    qs: qs,
  };
})();
