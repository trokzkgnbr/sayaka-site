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
  const v = SITE.assetVersion ? `?v=${SITE.assetVersion}` : '';
  const logoSrc = SITE.logo || '';
  const logo2x = SITE.logo2x || '';
  const logoAlt = SITE.artistNameEn || SITE.siteBrand || '';
  const logoW = SITE.logoWidth || 1024;
  const logoH = SITE.logoHeight || 267;
  const isSvg = logoSrc.endsWith('.svg');
  const srcset =
    logo2x && !isSvg ? ` srcset="${logoSrc}${v} 1x, ${logo2x}${v} 2x"` : '';
  brand.innerHTML = logoSrc
    ? `<img class="site-brand__img" src="${logoSrc}${v}"${srcset} alt="${logoAlt}" width="${logoW}" height="${logoH}">`
    : `<span class="site-brand__en">${SITE.artistNameEn}</span>`;
  brand.setAttribute('aria-label', `${SITE.artistNameJa} ${SITE.artistNameEn}`);
  header.prepend(brand);
}

const HEADER_SEGMENT_MELT_MAX_DELAY_MS = 10000;
const HEADER_SEGMENT_MELT_MS = 20000;

function finishHeaderMeltSegment(el) {
  el.classList.add('header-melt-segment--done');
}

function randomSegmentMeltDelayMs() {
  return Math.floor(Math.random() * (HEADER_SEGMENT_MELT_MAX_DELAY_MS + 1));
}

function applyHeaderSegmentMelt(el) {
  if (el.classList.contains('header-melt-segment')) return;

  const delayMs = randomSegmentMeltDelayMs();
  el.style.setProperty('--header-melt-delay', delayMs / 1000 + 's');
  el.classList.add('header-melt-segment');

  el.addEventListener('animationend', function (e) {
    if (e.animationName === 'header-segment-melt') finishHeaderMeltSegment(el);
  });

  window.setTimeout(function () {
    if (!el.classList.contains('header-melt-segment--done')) finishHeaderMeltSegment(el);
  }, delayMs + HEADER_SEGMENT_MELT_MS + 100);
}

/** バナー・メニュー・SNS を個別タイミングで消す（アニメーション終了までにじんで消える） */
function initHeaderSegmentMelt() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const segmentSelector =
    '.site-brand, .site-header .site-nav__link, .site-header .site-nav__submenu-link, .site-header .site-sns__link';
  const segments = document.querySelectorAll(
    window.matchMedia('(max-width: 760px)').matches
      ? segmentSelector
      : segmentSelector + ', .gallery-category-nav__link'
  );
  segments.forEach(applyHeaderSegmentMelt);
}

/** Home で計算した作品幅を profile / blog 等でも使う */
function initArtworkColumnWidth() {
  if (
    !document.body.classList.contains('page-inner') ||
    document.body.classList.contains('page-home')
  ) {
    return;
  }
  if (window.ArtworkSize && typeof ArtworkSize.restoreStoredMetrics === 'function') {
    ArtworkSize.restoreStoredMetrics();
  }
}

function initMain() {
  initSiteBrand();
  initHeaderSegmentMelt();
  initHeaderOnScroll();
  initYear();
  initFooterName();
  initArtworkColumnWidth();
}

function bootMain() {
  initMain();
  window.addEventListener('load', function () {
    window.setTimeout(initHeaderSegmentMelt, 0);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootMain);
} else {
  bootMain();
}
