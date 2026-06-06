/**
 * ギャラリー（縦1列・カテゴリ別）。
 * gallery.html?category=dawn または旧 URL（gallery-dawn.html 等）の data-gallery-category。
 */
const GALLERY_DEFAULT_CAPTION = {
  year: '2022',
  title: '今日からあなたは私だけの夢を見る',
  medium: 'oil on canvas',
  size: '1303 × 1940mm',
  poem: [
    '美しくて醜い魂が零れる滴のように',
    'いつしか蝶と呼ばれて',
    '天に還る',
  ],
};

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function getGallerySlug() {
  var fromBody = document.body.getAttribute('data-gallery-category');
  if (fromBody) return fromBody;
  var params = new URLSearchParams(window.location.search);
  var fromQuery = params.get('category');
  return fromQuery || 'dawn';
}

function resolveWorkCaption(work) {
  const base =
    (window.SITE && window.SITE.homeCaption) || GALLERY_DEFAULT_CAPTION;
  return {
    year: work.year || base.year,
    title: work.title || base.title,
    medium: work.medium || base.medium,
    size: work.size || base.size,
    poem: work.poem && work.poem.length ? work.poem : base.poem || [],
  };
}

function renderWorkMeta(work) {
  const cap = resolveWorkCaption(work);

  function lineHtml(text, cls) {
    return (
      '<span class="gallery__meta-line ' + cls + '">' + escapeHtml(text) + '</span>'
    );
  }

  function renderGroup(lines) {
    if (!lines.length) return '';
    return '<div class="gallery__meta-group">' + lines.join('') + '</div>';
  }

  const titleLines = [];
  if (cap.year) titleLines.push(lineHtml(cap.year, 'gallery__meta-year'));
  if (cap.title) titleLines.push(lineHtml(cap.title, 'gallery__meta-title'));

  const metaLines = [];
  if (cap.medium) metaLines.push(lineHtml(cap.medium, 'gallery__meta-medium'));
  if (cap.size) metaLines.push(lineHtml(cap.size, 'gallery__meta-size'));

  const poemLines = cap.poem.filter(Boolean).map(function (line) {
    return lineHtml(line, 'gallery__meta-poem');
  });

  return renderGroup(titleLines) + renderGroup(metaLines) + renderGroup(poemLines);
}

var galleryUniformFitSchedule = null;

/** 各作品を一画面に収め、最小の安全横幅に全画像を揃える */
function applyGalleryImageSize() {
  if (!window.ArtworkSize || typeof ArtworkSize.bindGalleryUniformFit !== 'function') {
    return;
  }
  galleryUniformFitSchedule = ArtworkSize.bindGalleryUniformFit();
}

function initGalleryCategoryNav() {
  var list = document.getElementById('gallery-category-nav');
  if (!list || !window.SITE || !SITE.galleryCategories) return;

  var current = getGallerySlug();
  list.replaceChildren();

  SITE.galleryCategories.forEach(function (cat) {
    var li = document.createElement('li');
    var link = document.createElement('a');
    link.className = 'gallery-category-nav__link';
    link.href = cat.href;
    link.textContent = cat.label;
    if (cat.slug === current) {
      link.classList.add('is-active');
      link.setAttribute('aria-current', 'page');
    }
    li.appendChild(link);
    list.appendChild(li);
  });
}

function renderGallery(series) {
  const root = document.getElementById('gallery');
  if (!root) return;

  if (!series || !series.works || !series.works.length) {
    root.innerHTML =
      '<p class="gallery-empty" role="status">このカテゴリは見つかりませんでした。</p>';
    return;
  }

  const titleEl = document.getElementById('gallery-page-title');
  if (titleEl) titleEl.textContent = series.title;
  document.title = series.title + ' | Gallery';

  const fragment = document.createDocumentFragment();

  if (series.intro && series.intro.length) {
    const introEl = document.createElement('div');
    introEl.className = 'gallery__intro';
    introEl.setAttribute('role', 'doc-foreword');
    series.intro.forEach(function (paragraph) {
      if (!paragraph) return;
      const p = document.createElement('p');
      p.className = 'gallery__intro-paragraph';
      p.textContent = paragraph;
      introEl.appendChild(p);
    });
    fragment.appendChild(introEl);
  }

  series.works.forEach(function (work, imageIndex) {
    const article = document.createElement('article');
    article.className = 'gallery__work';
    article.setAttribute('role', 'listitem');

    const img = document.createElement('img');
    img.className = 'gallery__img';
    img.src = work.src;
    img.alt = work.alt || '';
    img.loading = imageIndex < 2 ? 'eager' : 'lazy';
    img.decoding = 'async';
    article.appendChild(img);

    const meta = document.createElement('div');
    meta.className = 'gallery__meta';
    meta.innerHTML = renderWorkMeta(work);
    article.appendChild(meta);

    fragment.appendChild(article);
  });

  root.replaceChildren(fragment);
  applyGalleryImageSize();
}

function loadGallerySeries(slug) {
  var root = document.getElementById('gallery');
  if (!root) return Promise.resolve();

  root.innerHTML = '<p class="gallery-empty" role="status">読み込み中…</p>';

  return fetch('data/gallery-' + slug + '.json', { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('gallery data load failed');
      return res.json();
    })
    .then(function (series) {
      renderGallery(series);
    })
    .catch(function () {
      root.innerHTML =
        '<p class="gallery-empty" role="status">このカテゴリは見つかりませんでした。</p>';
    });
}

function initGalleryPage() {
  var slug = getGallerySlug();
  document.body.setAttribute('data-gallery-category', slug);
  initGalleryCategoryNav();
  loadGallerySeries(slug);
  window.addEventListener('resize', applyGalleryImageSize);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGalleryPage);
} else {
  initGalleryPage();
}
