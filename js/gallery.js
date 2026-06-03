/**
 * ギャラリー（縦1列・カテゴリ別ページ）。
 * body[data-gallery-category] で表示するシリーズを指定する。
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

const GALLERY_BY_SLUG = {
  dawn: {
    title: 'そして夜明けを拒むでしょう',
    works: [
      {
        src: 'images/home/main-visual.jpg',
        alt: '今日からあなたは私だけの夢を見る',
      },
      {
        src: 'images/gallery/sample-01.jpg',
        alt: '今日からあなたは私だけの夢を見る',
      },
      {
        src: 'images/gallery/sample-02.jpg',
        alt: '作品 02',
      },
    ],
  },
  dream: {
    title: 'Walk in a dream',
    works: [
      {
        src: 'images/gallery/sample-03.jpg',
        alt: '作品 03',
      },
    ],
  },
  colors: {
    title: '色彩の余白',
    works: [
      {
        src: 'images/gallery/sample-02.jpg',
        alt: '作品 04',
      },
      {
        src: 'images/gallery/sample-03.jpg',
        alt: '作品 05',
      },
    ],
  },
};

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
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

var galleryArtworkFitSchedule = null;

/** Home の fold と同じく、PC ではタイトル分だけ・スマホでは全文を高さ計算に使う */
function getGalleryLeadCaptionEl(leadWork) {
  if (!leadWork) return null;
  var mobile = window.matchMedia('(max-width: 760px)').matches;
  if (mobile) return leadWork.querySelector('.gallery__meta');
  return (
    leadWork.querySelector('.gallery__meta-group') ||
    leadWork.querySelector('.gallery__meta')
  );
}

function applyGalleryImageSize() {
  if (window.ArtworkSize) {
    ArtworkSize.restoreStoredMetrics();
  }
  fitGalleryLeadImage();
}

function fitGalleryLeadImage() {
  if (!window.ArtworkSize) return;

  var container = document.querySelector('.page-main--gallery');
  var leadWork = document.querySelector('.gallery__work');
  var leadImg = leadWork && leadWork.querySelector('.gallery__img');
  if (!container || !leadImg) return;

  function runFit() {
    if (galleryArtworkFitSchedule) {
      galleryArtworkFitSchedule();
      return;
    }
    galleryArtworkFitSchedule = ArtworkSize.bindStandardPageArtworkFit({
      container: container,
      img: leadImg,
      captionEl: getGalleryLeadCaptionEl(leadWork),
    });
  }

  if (leadImg.complete) runFit();
  else leadImg.addEventListener('load', runFit, { once: true });
}

function initGalleryCategoryNav() {
  var list = document.getElementById('gallery-category-nav');
  if (!list || !window.SITE || !SITE.galleryCategories) return;

  var current = document.body.getAttribute('data-gallery-category') || '';
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

function renderGallery() {
  const root = document.getElementById('gallery');
  if (!root) return;

  const slug = document.body.getAttribute('data-gallery-category') || 'dawn';
  const series = GALLERY_BY_SLUG[slug];

  if (!series) {
    root.innerHTML =
      '<p class="gallery-empty" role="status">このカテゴリは見つかりませんでした。</p>';
    return;
  }

  const titleEl = document.getElementById('gallery-page-title');
  if (titleEl) titleEl.textContent = series.title;
  document.title = series.title + ' | Gallery';

  const fragment = document.createDocumentFragment();

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

  galleryArtworkFitSchedule = null;
  root.replaceChildren(fragment);
  applyGalleryImageSize();
}

function initGalleryPage() {
  initGalleryCategoryNav();
  renderGallery();
  window.addEventListener('resize', applyGalleryImageSize);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initGalleryPage);
} else {
  initGalleryPage();
}
