function initHeaderOnScroll() {
  const header = document.getElementById('site-header');
  if (!header) return;
  const isHome = document.body.classList.contains('page-home');
  const onScroll = () => {
    header.classList.toggle('is-scrolled', window.scrollY > 8);
    if (isHome) {
      header.classList.remove('is-on-content');
    }
  };
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });
}

function initYear() {
  const y = document.getElementById('year');
  if (y) y.textContent = String(new Date().getFullYear());
}

function initFooterName() {
  const el = document.getElementById('footer-name');
  if (el && window.SITE) el.textContent = SITE.artistNameEn;
}

function initSiteBrand() {
  const header = document.getElementById('site-header');
  if (!header || !window.SITE) return;
  if (header.querySelector('.site-brand')) return;

  const brand = document.createElement('a');
  brand.className = 'site-brand';
  brand.href = 'index.html';
  brand.innerHTML = `<span class="site-brand__en">${SITE.artistNameEn}</span>`;
  brand.setAttribute('aria-label', `${SITE.artistNameJa} ${SITE.artistNameEn}`);
  header.prepend(brand);
}

const HEADER_SEGMENT_MELT_MAX_DELAY_MS = 13000;
const HEADER_SEGMENT_HIDE_MS = 30000;
const PAGE_LOAD_AT = Date.now();

function hideHeaderMeltEl(el) {
  el.style.pointerEvents = 'none';
  el.style.visibility = 'hidden';
}

function scheduleSegmentHideAt30s(el) {
  const elapsed = Date.now() - PAGE_LOAD_AT;
  const remaining = Math.max(0, HEADER_SEGMENT_HIDE_MS - elapsed);
  window.setTimeout(function () {
    hideHeaderMeltEl(el);
  }, remaining);
}

function randomSegmentMeltDelayMs() {
  return Math.floor(Math.random() * (HEADER_SEGMENT_MELT_MAX_DELAY_MS + 1));
}

function applyHeaderSegmentMelt(el) {
  if (el.classList.contains('header-melt-segment')) return;

  const delayMs = randomSegmentMeltDelayMs();
  el.style.setProperty('--header-melt-delay', delayMs / 1000 + 's');
  el.classList.add('header-melt-segment');
  scheduleSegmentHideAt30s(el);
}

/** バナー・メニュー・SNS を個別タイミングで消す（非表示は表示後30秒） */
function initHeaderSegmentMelt() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const segments = document.querySelectorAll(
    '.site-brand, .site-header .site-nav__link, .site-header .site-nav__submenu-link, .site-header .site-sns__link, .gallery-category-nav__link'
  );
  segments.forEach(applyHeaderSegmentMelt);
}

function initMain() {
  initSiteBrand();
  initHeaderSegmentMelt();
  initHeaderOnScroll();
  initYear();
  initFooterName();
}

function bootMain() {
  initMain();
  window.addEventListener('load', initHeaderSegmentMelt);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootMain);
} else {
  bootMain();
}
