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

  if (typeof window.applyHeaderSegmentMelt === 'function') {
    const meltTarget = brand.querySelector('.site-brand__img, .site-brand__en');
    if (meltTarget) window.applyHeaderSegmentMelt(meltTarget);
  }
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
  if (typeof window.initHeaderSegmentMelt === 'function') {
    window.initHeaderSegmentMelt();
  }
  initHeaderOnScroll();
  initYear();
  initFooterName();
  initArtworkColumnWidth();
}

function bootMain() {
  initMain();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootMain);
} else {
  bootMain();
}
