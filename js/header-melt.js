(function () {
  const HEADER_SEGMENT_MELT_MAX_DELAY_MS = 10000;
  const HEADER_SEGMENT_MELT_MS = 20000;
  const HEADER_MELT_SELECTOR =
    '.site-brand, .site-header .site-nav__link, .site-header .site-nav__submenu-link, .site-header .site-sns__link, .gallery-category-nav__link';

  function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function headerMeltSelector() {
    if (window.matchMedia('(max-width: 760px)').matches) {
      return HEADER_MELT_SELECTOR.replace(', .gallery-category-nav__link', '');
    }
    return HEADER_MELT_SELECTOR;
  }

  function primeHeaderMeltLook(el) {
    const root = getComputedStyle(document.documentElement);
    const opacity = root.getPropertyValue('--header-melt-initial-opacity').trim() || '0.827';
    const blur = root.getPropertyValue('--header-melt-initial-blur').trim() || '1.17px';
    el.style.setProperty('opacity', opacity);
    el.style.setProperty('filter', 'blur(' + blur + ')');
  }

  function clearHeaderMeltInline(el) {
    el.style.removeProperty('opacity');
    el.style.removeProperty('filter');
  }

  function finishHeaderMeltSegment(el) {
    el.classList.add('header-melt-segment--done');
    clearHeaderMeltInline(el);
  }

  function randomSegmentMeltDelayMs() {
    return Math.floor(Math.random() * (HEADER_SEGMENT_MELT_MAX_DELAY_MS + 1));
  }

  function bindHeaderMeltSegment(el, delayMs) {
    if (!el || el.dataset.headerMeltBound === '1') return;
    el.dataset.headerMeltBound = '1';

    el.addEventListener('animationend', function (e) {
      if (e.animationName === 'header-segment-melt') finishHeaderMeltSegment(el);
    });

    window.setTimeout(function () {
      if (!el.classList.contains('header-melt-segment--done')) finishHeaderMeltSegment(el);
    }, delayMs + HEADER_SEGMENT_MELT_MS + 100);
  }

  function applyHeaderSegmentMelt(el) {
    if (!el || el.classList.contains('header-melt-segment')) return;
    if (prefersReducedMotion()) return;

    primeHeaderMeltLook(el);

    const delayMs = randomSegmentMeltDelayMs();
    el.style.setProperty('--header-melt-delay', delayMs / 1000 + 's');
    el.classList.add('header-melt-segment');
    clearHeaderMeltInline(el);
    bindHeaderMeltSegment(el, delayMs);
  }

  function initHeaderSegmentMelt() {
    if (prefersReducedMotion()) return;
    document.querySelectorAll(headerMeltSelector()).forEach(applyHeaderSegmentMelt);
  }

  function observeHeaderMeltTargets() {
    const header = document.getElementById('site-header');
    const galleryNav = document.getElementById('gallery-category-nav');
    const roots = [header, galleryNav].filter(Boolean);
    if (!roots.length || prefersReducedMotion()) return;

    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType !== 1) return;
          if (node.matches && node.matches(headerMeltSelector())) {
            applyHeaderSegmentMelt(node);
          }
          if (node.querySelectorAll) {
            node.querySelectorAll(headerMeltSelector()).forEach(applyHeaderSegmentMelt);
          }
        });
      });
    });

    roots.forEach(function (root) {
      observer.observe(root, { childList: true, subtree: true });
    });
  }

  function scheduleHeaderMeltPasses() {
    initHeaderSegmentMelt();
    window.requestAnimationFrame(function () {
      initHeaderSegmentMelt();
      window.requestAnimationFrame(initHeaderSegmentMelt);
    });
  }

  window.applyHeaderSegmentMelt = applyHeaderSegmentMelt;
  window.initHeaderSegmentMelt = scheduleHeaderMeltPasses;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      scheduleHeaderMeltPasses();
      observeHeaderMeltTargets();
    });
  } else {
    scheduleHeaderMeltPasses();
    observeHeaderMeltTargets();
  }

  window.addEventListener('load', function () {
    window.setTimeout(scheduleHeaderMeltPasses, 0);
  });
})();
