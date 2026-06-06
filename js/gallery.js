/**
 * ギャラリー（縦1列・カテゴリ別）。
 * gallery.html?category=dawn または旧 URL（gallery-dawn.html 等）の data-gallery-category。
 */

var GALLERY_DEFAULT_CAPTION_ORDER = ['title', 'year', 'size', 'medium', 'poem'];

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
  return {
    title: work.title || '',
    year: work.year || '',
    size: work.size || '',
    medium: work.medium || '',
    poem: Array.isArray(work.poem) ? work.poem.slice() : [],
  };
}

function resolveCaptionOrder(work, series) {
  if (Array.isArray(work.captionOrder) && work.captionOrder.length) {
    return work.captionOrder;
  }
  if (Array.isArray(series.captionOrder) && series.captionOrder.length) {
    return series.captionOrder;
  }
  return GALLERY_DEFAULT_CAPTION_ORDER;
}

function captionLineClass(key) {
  return (
    {
      title: 'gallery__meta-title',
      year: 'gallery__meta-year',
      size: 'gallery__meta-size',
      medium: 'gallery__meta-medium',
      poem: 'gallery__meta-poem',
    }[key] || 'gallery__meta-line'
  );
}

function renderWorkMeta(work, series) {
  var cap = resolveWorkCaption(work);
  var order = resolveCaptionOrder(work, series || {});
  var groups = [];
  var current = [];

  function flushGroup() {
    if (!current.length) return;
    var isInfo = current.every(function (line) {
      return line.indexOf('gallery__meta-poem') === -1;
    });
    var cls = 'gallery__meta-group' + (isInfo ? ' gallery__meta-group--info' : '');
    groups.push('<div class="' + cls + '">' + current.join('') + '</div>');
    current = [];
  }

  function pushLine(text, cls) {
    current.push(
      '<span class="gallery__meta-line ' + cls + '">' + escapeHtml(text) + '</span>'
    );
  }

  order.forEach(function (key) {
    if (key === 'poem') {
      flushGroup();
      cap.poem.forEach(function (line) {
        if (line === '') {
          flushGroup();
          return;
        }
        pushLine(line, captionLineClass('poem'));
      });
      flushGroup();
      return;
    }

    var value = cap[key];
    if (!value) return;
    pushLine(value, captionLineClass(key));
  });

  flushGroup();
  return groups.join('');
}

var galleryUniformFitSchedule = null;

/** dawn 基準の共通横幅を全カテゴリに適用し、ディスプレイ中央に配置 */
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
    img.alt = work.alt || work.title || '';
    img.loading = imageIndex < 2 ? 'eager' : 'lazy';
    img.decoding = 'async';
    article.appendChild(img);

    const meta = document.createElement('div');
    meta.className = 'gallery__meta';
    meta.innerHTML = renderWorkMeta(work, series);
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
