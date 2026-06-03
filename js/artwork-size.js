(function () {
  var STORAGE_W = 'homeArtworkDisplayW';
  var STORAGE_H = 'homeArtworkDisplayH';
  var STORAGE_LEFT = 'homeArtworkDisplayLeft';

  function applyMetrics(metrics) {
    if (!metrics || metrics.width <= 0 || metrics.height <= 0) return;

    var wPx = Math.round(metrics.width) + 'px';
    var hPx = Math.round(metrics.height) + 'px';
    var leftPx =
      metrics.marginLeft != null ? Math.round(metrics.marginLeft) + 'px' : 'auto';

    document.documentElement.style.setProperty('--home-image-display-w', wPx);
    document.documentElement.style.setProperty('--home-image-display-h', hPx);
    document.documentElement.style.setProperty('--home-image-display-left', leftPx);

    try {
      sessionStorage.setItem(STORAGE_W, String(Math.round(metrics.width)));
      sessionStorage.setItem(STORAGE_H, String(Math.round(metrics.height)));
      if (metrics.marginLeft != null) {
        sessionStorage.setItem(STORAGE_LEFT, String(Math.round(metrics.marginLeft)));
      } else {
        sessionStorage.removeItem(STORAGE_LEFT);
      }
    } catch (e) {}
  }

  function restoreStoredMetrics() {
    var w = null;
    var h = null;
    var left = null;
    try {
      w = sessionStorage.getItem(STORAGE_W);
      h = sessionStorage.getItem(STORAGE_H);
      left = sessionStorage.getItem(STORAGE_LEFT);
    } catch (e) {}

    if (w) {
      document.documentElement.style.setProperty('--home-image-display-w', w + 'px');
    }
    if (h) {
      document.documentElement.style.setProperty('--home-image-display-h', h + 'px');
    }
    if (left) {
      document.documentElement.style.setProperty('--home-image-display-left', left + 'px');
    } else {
      document.documentElement.style.setProperty('--home-image-display-left', 'auto');
    }

    return !!(w && h);
  }

  function computeArtworkMetrics(container, img, captionEl, scaleFactor, options) {
    if (!container || !img || !img.naturalWidth || !img.naturalHeight) return null;

    options = options || {};
    var scale = scaleFactor == null ? 0.9 : scaleFactor;
    var containerStyle = getComputedStyle(container);
    var padX =
      parseFloat(containerStyle.paddingLeft) + parseFloat(containerStyle.paddingRight);
    var padY =
      parseFloat(containerStyle.paddingTop) + parseFloat(containerStyle.paddingBottom);
    var captionH = captionEl ? captionEl.getBoundingClientRect().height : 0;
    var availW;
    if (options.useUniformPageWidth) {
      var padXVal =
        parseFloat(
          getComputedStyle(document.documentElement).getPropertyValue('--artwork-pad-x')
        ) || 0;
      availW = window.innerWidth - 2 * padXVal;
    } else {
      availW = container.clientWidth - padX;
    }
    var availH;

    if (options.useViewportHeight) {
      var topPad =
        parseFloat(
          getComputedStyle(document.documentElement).getPropertyValue('--artwork-top-pad')
        ) || 0;
      var captionReserve = options.captionReserve || 0;
      availH = window.innerHeight - topPad - captionReserve - captionH;
    } else {
      availH = container.clientHeight - padY - captionH;
    }

    if (availW <= 0 || availH <= 0) return null;

    var fitScale =
      Math.min(availW / img.naturalWidth, availH / img.naturalHeight) * scale;
    var width = Math.floor(img.naturalWidth * fitScale);
    var height = Math.floor(img.naturalHeight * fitScale);

    var marginLeft;
    if (options.centerInContainer !== false) {
      marginLeft = (availW - width) / 2;
    } else {
      var containerRect = container.getBoundingClientRect();
      var imgRect = img.getBoundingClientRect();
      marginLeft = imgRect.left - containerRect.left;
    }

    return {
      width: width,
      height: height,
      marginLeft: marginLeft,
    };
  }

  function bindArtworkFit(options) {
    var container = options.container;
    var img = options.img;
    var captionEl = options.captionEl || null;
    var scaleFactor = options.scaleFactor;
    var fitOptions = options.fitOptions || {};
    var onMetrics = options.onMetrics;

    if (!container || !img) return function () {};

    function apply() {
      var metrics = computeArtworkMetrics(
        container,
        img,
        captionEl,
        scaleFactor,
        fitOptions
      );
      if (!metrics) return;
      applyMetrics(metrics);
      if (typeof onMetrics === 'function') onMetrics(metrics);
    }

    function schedule() {
      window.requestAnimationFrame(apply);
    }

    if (img.complete) schedule();
    else img.addEventListener('load', schedule);

    window.addEventListener('resize', schedule);
    if (typeof ResizeObserver !== 'undefined') {
      var observer = new ResizeObserver(schedule);
      observer.observe(container);
      if (captionEl) observer.observe(captionEl);
    }

    return schedule;
  }

  var STANDARD_SCALE = 0.9;
  var STANDARD_FIT_OPTIONS = {
    useViewportHeight: true,
    centerInContainer: true,
    useUniformPageWidth: true,
  };

  function bindStandardPageArtworkFit(options) {
    return bindArtworkFit({
      container: options.container,
      img: options.img,
      captionEl: options.captionEl || null,
      scaleFactor: options.scaleFactor != null ? options.scaleFactor : STANDARD_SCALE,
      fitOptions: options.fitOptions || STANDARD_FIT_OPTIONS,
      onMetrics: options.onMetrics,
    });
  }

  window.ArtworkSize = {
    applyMetrics: applyMetrics,
    restoreStoredMetrics: restoreStoredMetrics,
    computeArtworkMetrics: computeArtworkMetrics,
    bindArtworkFit: bindArtworkFit,
    bindStandardPageArtworkFit: bindStandardPageArtworkFit,
    STANDARD_SCALE: STANDARD_SCALE,
  };
})();
