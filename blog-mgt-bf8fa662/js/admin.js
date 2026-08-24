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
      window.location.href = "login.html";
      return false;
    }
  }

  async function login(password) {
    await api("api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: password }),
    });
    return true;
  }

  async function logout() {
    try {
      await api("api/logout", { method: "POST" });
    } catch (_err) {
      /* ignore */
    }
    window.location.href = "login.html";
  }

  var IMAGE_MAX_EDGE = 1600;
  var IMAGE_TARGET_BYTES = 900 * 1024;
  var IMAGE_HARD_MAX_BYTES = 1.5 * 1024 * 1024;

  function canvasToJpegBlob(canvas, quality) {
    return new Promise(function (resolve, reject) {
      canvas.toBlob(
        function (blob) {
          if (blob) resolve(blob);
          else reject(new Error("画像の圧縮に失敗しました"));
        },
        "image/jpeg",
        quality
      );
    });
  }

  async function loadImageSource(file) {
    if (typeof createImageBitmap === "function") {
      try {
        return await createImageBitmap(file, { imageOrientation: "from-image" });
      } catch (_err) {
        /* fall through */
      }
    }
    return new Promise(function (resolve, reject) {
      var url = URL.createObjectURL(file);
      var img = new Image();
      img.onload = function () {
        URL.revokeObjectURL(url);
        resolve(img);
      };
      img.onerror = function () {
        URL.revokeObjectURL(url);
        reject(new Error("この画像は使えません。JPEG / PNG / WebP で選び直してください。"));
      };
      img.src = url;
    });
  }

  async function prepareImage(file) {
    if (!file) throw new Error("画像を選んでください");
    var source = await loadImageSource(file);
    var width = source.width || source.naturalWidth || 0;
    var height = source.height || source.naturalHeight || 0;
    if (!width || !height) throw new Error("画像を読み込めませんでした");

    var scale = Math.min(1, IMAGE_MAX_EDGE / Math.max(width, height));
    var canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(width * scale));
    canvas.height = Math.max(1, Math.round(height * scale));
    var ctx = canvas.getContext("2d", { alpha: false });
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
    if (typeof source.close === "function") source.close();

    var quality = 0.82;
    var blob = await canvasToJpegBlob(canvas, quality);
    while (blob.size > IMAGE_TARGET_BYTES && quality > 0.5) {
      quality -= 0.08;
      blob = await canvasToJpegBlob(canvas, quality);
    }
    if (blob.size > IMAGE_HARD_MAX_BYTES) {
      throw new Error("画像が大きすぎます。別の写真を選ぶか、もう少し小さい画像にしてください。");
    }
    return new File([blob], "photo.jpg", { type: "image/jpeg" });
  }

  async function checkGithub() {
    try {
      return await api("api/health");
    } catch (err) {
      return { ok: false, github: false, error: err.message };
    }
  }

  window.DiaryAdmin = {
    api: api,
    showMessage: showMessage,
    ensureAuth: ensureAuth,
    login: login,
    logout: logout,
    prepareImage: prepareImage,
    checkGithub: checkGithub,
    qs: qs,
  };
})();
