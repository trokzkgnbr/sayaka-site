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
        src: 'images/gallery/dawn/01.jpg',
        alt: 'そして夜明けを拒むでしょう',
        title: 'そして夜明けを拒むでしょう',
        year: '2021年度　卒業制作',
        poem: [
          '今日はいつもとは違う道',
          '花束を抱えて鯨の後ろを追いかけた',
          'タプタプのコップに浮かべて',
          '黄金の中に縁がちらちら泳いでいる',
          'まだ行かないよ',
          'やがて丸く消えていく',
          '結末を揺らして通り過ぎていく',
          '空を見上げたら月を探すから',
          '真っ暗な夜も埋め尽くすほど',
          'あなたの光になってあげる',
          '美しくて醜い魂が零れる滴のように',
          'いつしか蝶と呼ばれて',
          '天に還る',
        ],
      },
      {
        src: 'images/gallery/dawn/02.jpg',
        alt: 'いつもあたたかく瞬く',
        title: 'いつもあたたかく瞬く',
        size: '455×606mm',
        medium: 'oil, charcoal on canvas',
        poem: [
          '「何処に行くの」まだいかないよ',
          '「此処に居ないの」まだいかないよ',
          '「何処か行くの」まだいかないよ',
          '「もう行くの」まだいかないよ',
          '「何時行くの」まだいかないよ',
          '「まだ行かないの」まだ行かないよ',
        ],
      },
      {
        src: 'images/gallery/dawn/03.jpg',
        alt: '夜空を飛んであなたの夜の中へ',
        title: '夜空を飛んであなたの夜の中へ',
        size: '1303×1940mm',
        medium: 'oil on canvas',
        poem: [
          '空を見上げたら月を探すから',
          '真っ暗な夜もうめつくすほど',
          'あなたの光になってあげる',
        ],
      },
      {
        src: 'images/gallery/dawn/04.jpg',
        alt: '今日からあなたはわたしの夢だけをみる',
        title: '今日からあなたはわたしの夢だけをみる',
        size: '1303×1940mm',
        medium: 'oil on canvas',
        poem: [
          '美しくて醜い魂が零れる滴のように',
          'いつしか蝶に呼ばれて',
          '天に還る',
        ],
      },
      {
        src: 'images/gallery/dawn/05.jpg',
        alt: '星の数と同じだけ',
        title: '星の数と同じだけ',
        size: '410×318mm',
        medium: 'oil, charcoal, pastel on canvas',
        poem: [
          'ちいちゃな星のかけらを',
          'ちいちゃなおててで掬いあげた',
          'ふらふらと揺れる魚と',
          '銀の線に手を引かれて',
          'こんもりとした銀の砂の山の上に着いた',
          'タプタプのコップに浮かべて',
          '空を泳いだら',
          '紙飛行機に乗って',
          'またねをした',
        ],
      },
      {
        src: 'images/gallery/dawn/06.jpg',
        alt: '満ちる途中',
        title: '満ちる途中',
        size: '300×400mm',
        medium: 'oil, charcoal on canvas',
        poem: [
          '風はいつも通り過ぎて',
          '回り道をする',
          '空っぽなお風呂はだんだんお湯が溢れて',
          '緩いところから少しずつ',
          '他のところに浸透していく',
          'ひとつ階層が上がると',
          '静かな蝋燭が',
          '目前に脆さと強さを兼ね備えて待っている',
          'そして',
          'やがて丸く消えていく',
          '結末を揺らして通り過ぎていく',
        ],
      },
      {
        src: 'images/gallery/dawn/07.jpg',
        alt: 'walk in a dream',
        title: 'walk in a dream',
        size: '300×400mm',
      },
      {
        src: 'images/gallery/dawn/08.jpg',
        alt: 'あの遠くにある木の中の後ろ',
        title: 'あの遠くにある木の中の後ろ',
        size: '1303×1940mm',
        medium: 'oil, charcoal on canvas',
        poem: [
          '毎日みる風景',
          '今日はいつもとは違う道',
          '大きな木を越えると',
          'また次の木の根が這っている',
          '小さなトロッコに乗って水の上を走って',
          '雲の中を飛び越えて',
          '花束を抱えて鯨の後を追いかけた',
          '流れ星が落ちてきて手の上で居眠りしている',
          '丘の上のグレーの中は',
          'いつもよりちょっとだけ雪がまっていた',
        ],
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
