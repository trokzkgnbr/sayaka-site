(function () {
  const root = document.getElementById('diary-post');
  if (!root) return;

  const params = new URLSearchParams(window.location.search);
  const postId = params.get('id');

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatDate(isoDate) {
    const value = String(isoDate || '').trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return value.replace(/-/g, '/');
    }
    const d = new Date(value.includes('T') ? value : value + 'T12:00:00');
    if (Number.isNaN(d.getTime())) return value;
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return y + '/' + m + '/' + day;
  }

  /** 1行目はタイトル用なので本文表示から除外 */
  function bodyWithoutTitleLine(text) {
    var lines = String(text || '').split(/\r?\n/);
    if (!lines.length) return '';
    lines.shift();
    while (lines.length && !lines[0].trim()) lines.shift();
    return lines.join('\n');
  }

  function renderBody(text) {
    var trimmed = String(text || '').trim();
    if (!trimmed) return '';
    return escapeHtml(text)
      .split(/\n\n+/)
      .map(function (block) {
        return '<p>' + block.replace(/\n/g, '<br>') + '</p>';
      })
      .join('');
  }

  function setPageTitle() {
    if (window.SITE && typeof SITE.pageTitle === 'function') {
      document.title = SITE.pageTitle('blog');
      return;
    }
    document.title = 'SAYAYOSUI｜blog';
  }

  function showError(message) {
    root.innerHTML =
      '<p class="diary-empty" role="alert">' +
      escapeHtml(message) +
      '</p>' +
      '<p class="diary-back-wrap"><a class="diary-back" href="diary.html">blog 一覧へ</a></p>';
    setPageTitle();
  }

  if (!postId) {
    showError('投稿が指定されていません。');
    return;
  }

  fetch('data/diary.json', { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('diary.json load failed');
      return res.json();
    })
    .then(function (data) {
      const post = (data.posts || []).find(function (p) {
        return p.id === postId;
      });
      if (!post) {
        showError('投稿が見つかりませんでした。');
        return;
      }

      setPageTitle();

      root.innerHTML =
        '<p class="diary-back-wrap"><a class="diary-back" href="diary.html">← blog 一覧</a></p>' +
        '<div class="diary-detail__content">' +
        '<figure class="diary-detail__figure">' +
        '<img src="' +
        escapeHtml(post.image) +
        '" alt="" width="360" height="360" loading="eager" decoding="async">' +
        '</figure>' +
        '<div class="diary-detail__main">' +
        '<header class="diary-detail__head">' +
        '<h1 class="diary-detail__title">' +
        escapeHtml(post.title) +
        '</h1>' +
        '<time class="diary-detail__date" datetime="' +
        escapeHtml(post.date) +
        '">' +
        escapeHtml(formatDate(post.date)) +
        '</time>' +
        '</header>' +
        '<div class="diary-detail__body prose">' +
        renderBody(bodyWithoutTitleLine(post.body)) +
        '</div>' +
        '</div>' +
        '</div>';
    })
    .catch(function () {
      showError('ブログを読み込めませんでした。');
    });
})();
