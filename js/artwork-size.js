(function () {
  var STORAGE_W = 'homeArtworkDisplayW';
  var STORAGE_H = 'homeArtworkDisplayH';

  function applyMetrics(metrics) {
    if (!metrics || metrics.width <= 0 || metrics.height <= 0) return;

    if (window.LayoutMetrics && typeof LayoutMetrics.applyMeasured === 'function') {
      LayoutMetrics.applyMeasured(metrics.width, metrics.height);
      return;
    }

    var wPx = Math.round(metrics.width) + 'px';
    var hPx = Math.round(metrics.height) + 'px';

    document.documentElement.style.setProperty('--home-image-display-w', wPx);
    document.documentElement.style.setProperty('--home-image-display-h', hPx);

    try {
      sessionStorage.setItem(STORAGE_W, String(Math.round(metrics.width)));
      sessionStorage.setItem(STORAGE_H, String(Math.round(metrics.height)));
      sessionStorage.setItem('homeArtworkViewportW', String(window.innerWidth));
      sessionStorage.removeItem('homeArtworkDisplayLeft');
    } catch (e) {}
  }

  function restoreStoredMetrics() {
    if (window.LayoutMetrics && typeof LayoutMetrics.restoreOrCompute === 'function') {
      LayoutMetrics.restoreOrCompute();
      return true;
    }

    var w = null;
    var h = null;
    var vw = null;
    try {
      w = sessionStorage.getItem(STORAGE_W);
      h = sessionStorage.getItem(STORAGE_H);
      vw = sessionStorage.getItem('homeArtworkViewportW');
    } catch (e) {}

    if (vw && String(window.innerWidth) !== String(parseInt(vw, 10))) {
      return false;
    }

    if (w) {
      document.documentElement.style.setProperty('--home-image-display-w', w + 'px');
    }
    if (h) {
      document.documentElement.style.setProperty('--home-image-display-h', h + 'px');
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
    var captionMin = options.captionMinReserve || 0;
    if (captionMin > 0) {
      captionH = Math.max(captionH, captionMin);
    }
    var availW;
    if (options.useUniformPageWidth) {
      var padXVal = readRootPxVar('--artwork-pad-x', 0);
      availW = window.innerWidth - 2 * padXVal;
    } else {
      availW = container.clientWidth - padX;
    }
    var availH;

    if (options.useViewportHeight) {
      var topPad = readRootPxVar('--artwork-top-pad', 0);
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

    return {
      width: width,
      height: height,
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
  /** @deprecated Gallery は bindGalleryUniformFit を使用 */
  var GALLERY_HOME_WIDTH_RATIO = 0.9;
  var STANDARD_FIT_OPTIONS = {
    useViewportHeight: true,
    useUniformPageWidth: true,
  };

  var galleryUniformFitResizeBound = false;
  var galleryUniformFitGalleryObserver = null;
  var GALLERY_REFERENCE_SLUG = 'dawn';
  var STORAGE_GALLERY_REF_W = 'galleryReferenceDisplayW';
  var galleryReferenceImagesCache = null;
  var galleryReferenceImagesPromise = null;

  function readRootPxVar(name, fallback) {
    var raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    if (raw.endsWith('px')) {
      var parsed = parseFloat(raw);
      if (parsed > 0) return parsed;
    }
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

  function getGalleryAvailWidth() {
    var padX = readRootPxVar('--artwork-pad-x', 12);
    return Math.max(0, window.innerWidth - 2 * padX);
  }

  function workHasDimensions(work) {
    return work && work.width > 0 && work.height > 0;
  }

  function dimensionsToImageStub(work) {
    return {
      naturalWidth: work.width,
      naturalHeight: work.height,
    };
  }

  function preloadGalleryImage(src) {
    return new Promise(function (resolve) {
      var img = new Image();
      img.onload = function () {
        resolve(img);
      };
      img.onerror = function () {
        resolve(null);
      };
      img.src = src;
    });
  }

  function loadGalleryReferenceImages() {
    if (galleryReferenceImagesCache) {
      return Promise.resolve(galleryReferenceImagesCache);
    }
    if (galleryReferenceImagesPromise) {
      return galleryReferenceImagesPromise;
    }

    galleryReferenceImagesPromise = fetch('data/gallery-' + GALLERY_REFERENCE_SLUG + '.json')
      .then(function (res) {
        if (!res.ok) throw new Error('gallery reference data load failed');
        return res.json();
      })
      .then(function (data) {
        var works = data.works || [];
        if (works.length && works.every(workHasDimensions)) {
          galleryReferenceImagesCache = works.map(dimensionsToImageStub);
          return galleryReferenceImagesCache;
        }
        return Promise.all(
          works.map(function (work) {
            return preloadGalleryImage(work.src);
          })
        ).then(function (images) {
          galleryReferenceImagesCache = images.filter(function (img) {
            return img && img.naturalWidth > 0;
          });
          return galleryReferenceImagesCache;
        });
      })
      .catch(function () {
        galleryReferenceImagesCache = [];
        return galleryReferenceImagesCache;
      });

    return galleryReferenceImagesPromise;
  }

  function getGalleryViewportAvailHeight() {
    var topPad = readRootPxVar('--artwork-top-pad', 80);
    var bottomReserve = 20;
    return Math.max(0, window.innerHeight - topPad - bottomReserve);
  }

  /** 画像だけが一画面（高さ）に収まる最大横幅 */
  function maxGalleryWidthForWork(img, availW, availH) {
    if (!img || !img.naturalWidth || !img.naturalHeight) return 0;
    var aspect = img.naturalWidth / img.naturalHeight;
    var maxW = Math.floor(availW);
    var maxFromHeight = Math.floor(availH * aspect);
    if (maxW < 1 || maxFromHeight < 1) return 0;
    return Math.min(maxW, maxFromHeight);
  }

  function applyGalleryImageHeights(works, unifiedWidth) {
    for (var i = 0; i < works.length; i++) {
      var img = works[i].querySelector('.gallery__img');
      if (!img || !img.naturalWidth || !img.naturalHeight) continue;
      var height = Math.floor(unifiedWidth * (img.naturalHeight / img.naturalWidth));
      var heightPx = Math.max(1, height) + 'px';
      img.style.width = '100%';
      img.style.height = heightPx;
      img.style.maxHeight = heightPx;
    }
  }

  function computeGalleryReferenceWidth(images, availW, availH) {
    if (!images || !images.length) return null;
    var widths = [];
    for (var i = 0; i < images.length; i++) {
      widths.push(maxGalleryWidthForWork(images[i], availW, availH));
    }
    widths = widths.filter(function (w) {
      return w > 0;
    });
    if (!widths.length) return null;
    return Math.max(1, Math.min.apply(null, widths));
  }

  function storeGalleryReferenceWidth(width) {
    try {
      sessionStorage.setItem(STORAGE_GALLERY_REF_W, String(Math.round(width)));
    } catch (e) {}
  }

  function restoreGalleryReferenceWidth() {
    try {
      var stored = sessionStorage.getItem(STORAGE_GALLERY_REF_W);
      if (!stored) return null;
      var width = parseInt(stored, 10);
      if (!(width > 0)) return null;
      document.documentElement.style.setProperty(
        '--gallery-image-display-w',
        width + 'px'
      );
      return width;
    } catch (e) {
      return null;
    }
  }

  function markGallerySized() {
    if (document.body) {
      document.body.classList.add('is-gallery-sized');
    }
  }

  function clearGallerySizedState() {
    if (document.body) {
      document.body.classList.remove('is-gallery-sized');
    }
  }

  function resolveGalleryReferenceWidth() {
    var availW = getGalleryAvailWidth();
    var availH = getGalleryViewportAvailHeight();
    if (availW <= 0 || availH <= 0) {
      return Promise.resolve(null);
    }

    return loadGalleryReferenceImages().then(function (images) {
      var unified = computeGalleryReferenceWidth(images, availW, availH);
      if (unified) storeGalleryReferenceWidth(unified);
      return unified;
    });
  }

  function applyGalleryUniformFit() {
    restoreGalleryReferenceWidth();
    return resolveGalleryReferenceWidth().then(function (unified) {
      if (!unified) return false;

      document.documentElement.style.setProperty(
        '--gallery-image-display-w',
        unified + 'px'
      );

      var works = document.querySelectorAll('.page-main--gallery .gallery__work');
      if (!works.length) {
        markGallerySized();
        return true;
      }

      applyGalleryImageHeights(works, unified);
      markGallerySized();
      return true;
    });
  }

  function bindGalleryUniformFit() {
    restoreGalleryReferenceWidth();

    function schedule() {
      restoreGalleryReferenceWidth();
      window.requestAnimationFrame(function () {
        applyGalleryUniformFit().then(function (applied) {
          if (applied) return;
          var pending = document.querySelectorAll('.page-main--gallery .gallery__img');
          for (var i = 0; i < pending.length; i++) {
            var img = pending[i];
            if (img.complete && img.naturalWidth) continue;
            img.addEventListener('load', schedule, { once: true });
          }
        });
      });
    }

    if (!galleryUniformFitResizeBound) {
      galleryUniformFitResizeBound = true;
      window.addEventListener('resize', schedule);
    }

    var gallery = document.getElementById('gallery');
    if (typeof ResizeObserver !== 'undefined') {
      if (!galleryUniformFitGalleryObserver) {
        galleryUniformFitGalleryObserver = new ResizeObserver(schedule);
      }
      galleryUniformFitGalleryObserver.disconnect();
      if (gallery) galleryUniformFitGalleryObserver.observe(gallery);
    }

    schedule();
    return schedule;
  }

  function getHomeDisplayWidthPx() {
    restoreStoredMetrics();
    var w = parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue('--home-image-display-w')
    );
    return w > 0 ? w : null;
  }

  function applyGalleryDisplayWidth(homeWidthPx) {
    var w = Math.max(1, Math.round(homeWidthPx * GALLERY_HOME_WIDTH_RATIO));
    document.documentElement.style.setProperty('--gallery-image-display-w', w + 'px');
    return w;
  }

  function measureHomeCaptionMinReserve() {
    var fromCss = parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue('--home-caption-fold-min-h')
    );
    return fromCss > 0 ? fromCss : 80;
  }

  function resolveGalleryDisplayWidth(options) {
    options = options || {};
    var homeSrc = options.homeSrc || '';
    var preload = options.preloadImage || null;

    function finish(homeW) {
      if (homeW > 0) applyGalleryDisplayWidth(homeW);
      if (typeof options.onMetrics === 'function') options.onMetrics(homeW);
    }

    function computeFromImage(img) {
      var metrics = computeArtworkMetrics(
        document.documentElement,
        img,
        null,
        STANDARD_SCALE,
        {
          useUniformPageWidth: true,
          useViewportHeight: true,
          captionMinReserve: measureHomeCaptionMinReserve(),
        }
      );
      if (metrics && metrics.width > 0) finish(metrics.width);
    }

    function run() {
      var stored = getHomeDisplayWidthPx();
      if (stored) {
        finish(stored);
        return;
      }
      if (preload && preload.naturalWidth) {
        computeFromImage(preload);
        return;
      }
      if (!homeSrc) return;
      if (!options._loader) {
        options._loader = new Image();
        options._loader.addEventListener(
          'load',
          function () {
            computeFromImage(options._loader);
          },
          { once: false }
        );
        options._loader.src = homeSrc;
      } else if (options._loader.complete && options._loader.naturalWidth) {
        computeFromImage(options._loader);
      }
    }

    run();
    window.addEventListener('resize', run);
    return run;
  }

  function bindStandardPageArtworkFit(options) {
    var fitOptions = Object.assign({}, STANDARD_FIT_OPTIONS, options.fitOptions || {});
    return bindArtworkFit({
      container: options.container,
      img: options.img,
      captionEl: options.captionEl || null,
      scaleFactor: options.scaleFactor != null ? options.scaleFactor : STANDARD_SCALE,
      fitOptions: fitOptions,
      onMetrics: options.onMetrics,
    });
  }

  window.ArtworkSize = {
    applyMetrics: applyMetrics,
    restoreStoredMetrics: restoreStoredMetrics,
    computeArtworkMetrics: computeArtworkMetrics,
    bindArtworkFit: bindArtworkFit,
    bindStandardPageArtworkFit: bindStandardPageArtworkFit,
    resolveGalleryDisplayWidth: resolveGalleryDisplayWidth,
    applyGalleryDisplayWidth: applyGalleryDisplayWidth,
    bindGalleryUniformFit: bindGalleryUniformFit,
    applyGalleryUniformFit: applyGalleryUniformFit,
    restoreGalleryReferenceWidth: restoreGalleryReferenceWidth,
    clearGallerySizedState: clearGallerySizedState,
    resolveGalleryReferenceWidth: resolveGalleryReferenceWidth,
    GALLERY_REFERENCE_SLUG: GALLERY_REFERENCE_SLUG,
    STANDARD_SCALE: STANDARD_SCALE,
    GALLERY_HOME_WIDTH_RATIO: GALLERY_HOME_WIDTH_RATIO,
  };
})();
