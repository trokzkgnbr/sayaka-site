(function () {
  const root = document.getElementById('diary-post');
  if (!root) return;

  const params = new URLSearchParams(window.location.search);
  const postId = params.get('id');

  const dateFmt = new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatDate(isoDate) {
    const d = new Date(isoDate + 'T12:00:00');
    if (Number.isNaN(d.getTime())) return isoDate;
    return dateFmt.format(d);
  }

  function renderBody(text) {
    return escapeHtml(text)
      .split(/\n\n+/)
      .map(function (block) {
        return '<p>' + block.replace(/\n/g, '<br>') + '</p>';
      })
      .join('');
  }

  function showError(message) {
    root.innerHTML =
      '<p class="diary-empty" role="alert">' +
      escapeHtml(message) +
      '</p>' +
      '<p class="diary-back-wrap"><a class="diary-back" href="diary.html">Diary 一覧へ</a></p>';
    document.title = 'Diary | Portfolio';
  }

  if (!postId) {
    showError('投稿が指定されていません。');
    return;
  }

  fetch('data/diary.json')
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

      document.title = post.title + ' | Diary';

      root.innerHTML =
        '<p class="diary-back-wrap"><a class="diary-back" href="diary.html">← Diary 一覧</a></p>' +
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
        '<figure class="diary-detail__figure">' +
        '<img src="' +
        escapeHtml(post.image) +
        '" alt="" width="960" height="960" loading="eager" decoding="async">' +
        '</figure>' +
        '<div class="diary-detail__body prose">' +
        renderBody(post.body) +
        '</div>';
    })
    .catch(function () {
      showError('日記を読み込めませんでした。');
    });
})();
