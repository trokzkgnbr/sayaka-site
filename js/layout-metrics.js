/**
 * 初回描画前にホーム作品幅と左余白を確定する。
 * sessionStorage は同じviewport幅のときだけ使い、それ以外は画像比から計算する。
 */
(function () {
  var STORAGE_W = 'homeArtworkDisplayW';
  var STORAGE_H = 'homeArtworkDisplayH';
  var STORAGE_VW = 'homeArtworkViewportW';
  var HOME_NW = 2400;
  var HOME_NH = 1607;
  var SCALE = 0.9;

  function readCssPx(name, fallback) {
    var probe = document.createElement('div');
    probe.style.cssText =
      'position:absolute;left:-9999px;top:0;height:0;pointer-events:none;width:var(' +
      name +
      ')';
    document.documentElement.appendChild(probe);
    var px = probe.getBoundingClientRect().width;
    document.documentElement.removeChild(probe);
    return px > 0 ? px : fallback;
  }

  function isMobileViewport() {
    return window.innerWidth <= 760;
  }

  function apply(w, h, save) {
    w = Math.max(1, Math.round(w));
    h = Math.max(1, Math.round(h));
    var root = document.documentElement;
    root.style.setProperty('--home-image-display-w', w + 'px');
    root.style.setProperty('--home-image-display-h', h + 'px');
    var pad = readCssPx('--artwork-pad-x', 6);
    var left = Math.max(pad, Math.round((window.innerWidth - w) / 2));
    root.style.setProperty('--page-align-left', left + 'px');
    if (save) {
      try {
        sessionStorage.setItem(STORAGE_W, String(w));
        sessionStorage.setItem(STORAGE_H, String(h));
        sessionStorage.setItem(STORAGE_VW, String(window.innerWidth));
      } catch (e) {}
    }
  }

  function compute() {
    var pad = readCssPx('--artwork-pad-x', 6);
    var availW = window.innerWidth - 2 * pad;
    if (availW < 1) availW = window.innerWidth;
    if (isMobileViewport()) {
      apply(availW, availW * (HOME_NH / HOME_NW), false);
      return;
    }
    var top = readCssPx('--artwork-top-pad', 80);
    var cap = readCssPx('--home-caption-fold-min-h', 0);
    var availH = window.innerHeight - top - cap;
    if (availH < 1) availH = window.innerHeight;
    var scale = Math.min(availW / HOME_NW, availH / HOME_NH) * SCALE;
    apply(HOME_NW * scale, HOME_NH * scale, false);
  }

  function restoreOrCompute() {
    try {
      var w = parseInt(sessionStorage.getItem(STORAGE_W), 10);
      var h = parseInt(sessionStorage.getItem(STORAGE_H), 10);
      var vw = parseInt(sessionStorage.getItem(STORAGE_VW), 10);
      var pad = readCssPx('--artwork-pad-x', 6);
      var maxW = window.innerWidth - 2 * pad;
      if (
        w > 40 &&
        h > 40 &&
        vw === window.innerWidth &&
        w <= window.innerWidth &&
        (maxW < 1 || w <= maxW + 2)
      ) {
        apply(w, h, false);
        return;
      }
    } catch (e) {}
    compute();
  }

  restoreOrCompute();

  var lastViewportW = window.innerWidth;
  var resizeTimer = 0;
  window.addEventListener('resize', function () {
    if (isMobileViewport() && window.innerWidth === lastViewportW) return;
    lastViewportW = window.innerWidth;
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(restoreOrCompute, 50);
  });

  window.LayoutMetrics = {
    applyMeasured: function (w, h) {
      apply(w, h, true);
    },
    restoreOrCompute: restoreOrCompute,
  };
})();
