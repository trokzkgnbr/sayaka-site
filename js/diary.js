(function () {
  const listEl = document.getElementById('diary-list');
  if (!listEl) return;

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

  function postHref(id) {
    return 'diary-post.html?id=' + encodeURIComponent(id);
  }

  function renderCard(post) {
    const href = postHref(post.id);
    const title = escapeHtml(post.title);
    const date = escapeHtml(formatDate(post.date));
    const img = escapeHtml(post.image);
    const alt = escapeHtml(post.title);

    return (
      '<article class="diary-card" role="listitem">' +
      '<a class="diary-card__link" href="' +
      href +
      '">' +
      '<span class="diary-card__thumb">' +
      '<img src="' +
      img +
      '" alt="" width="320" height="320" loading="lazy" decoding="async">' +
      '</span>' +
      '<span class="diary-card__body">' +
      '<h2 class="diary-card__title">' +
      title +
      '</h2>' +
      '<time class="diary-card__date" datetime="' +
      escapeHtml(post.date) +
      '">' +
      date +
      '</time>' +
      '</span>' +
      '</a>' +
      '</article>'
    );
  }

  function showEmpty(message) {
    listEl.innerHTML =
      '<p class="diary-empty" role="status">' + escapeHtml(message) + '</p>';
  }

  fetch('data/diary.json')
    .then(function (res) {
      if (!res.ok) throw new Error('diary.json load failed');
      return res.json();
    })
    .then(function (data) {
      const posts = (data.posts || []).slice().sort(function (a, b) {
        return b.date.localeCompare(a.date);
      });
      if (!posts.length) {
        showEmpty('まだ投稿がありません。');
        return;
      }
      listEl.innerHTML = posts.map(renderCard).join('');
    })
    .catch(function () {
      showEmpty('日記を読み込めませんでした。');
    });
})();
