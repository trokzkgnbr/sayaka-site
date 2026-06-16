(function () {
  const listEl = document.getElementById('diary-list');
  const paginationEl = document.getElementById('diary-pagination');
  if (!listEl) return;

  const PAGE_SIZE = 30;

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

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function postHref(id) {
    return 'diary-post.html?id=' + encodeURIComponent(id);
  }

  function getPageNumber() {
    const raw = new URLSearchParams(window.location.search).get('page');
    const n = parseInt(raw || '1', 10);
    return Number.isFinite(n) && n > 0 ? n : 1;
  }

  function pageHref(page) {
    if (page <= 1) return 'diary.html';
    return 'diary.html?page=' + page;
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
    if (paginationEl) {
      paginationEl.hidden = true;
      paginationEl.innerHTML = '';
    }
  }

  function renderPagination(page, totalPages) {
    if (!paginationEl) return;
    if (totalPages <= 1) {
      paginationEl.hidden = true;
      paginationEl.innerHTML = '';
      return;
    }

    paginationEl.hidden = false;
    var parts = [];

    if (page > 1) {
      parts.push(
        '<a class="diary-pagination__link diary-pagination__link--prev" href="' +
          escapeHtml(pageHref(page - 1)) +
          '">← prev</a>'
      );
    }

    parts.push(
      '<span class="diary-pagination__status">' +
        page +
        ' / ' +
        totalPages +
        '</span>'
    );

    if (page < totalPages) {
      parts.push(
        '<a class="diary-pagination__link diary-pagination__link--next" href="' +
          escapeHtml(pageHref(page + 1)) +
          '">next →</a>'
      );
    }

    paginationEl.innerHTML = parts.join('');
  }

  function sortPostsByDate(posts) {
    return posts.slice().sort(function (a, b) {
      var byDate = (b.date || '').localeCompare(a.date || '');
      if (byDate !== 0) return byDate;
      return (b.publishedAt || '').localeCompare(a.publishedAt || '');
    });
  }

  function renderPage(posts, page) {
    const totalPages = Math.max(1, Math.ceil(posts.length / PAGE_SIZE));
    const safePage = Math.min(page, totalPages);
    const start = (safePage - 1) * PAGE_SIZE;
    const slice = posts.slice(start, start + PAGE_SIZE);

    if (safePage !== page) {
      window.location.replace(pageHref(safePage));
      return;
    }

    listEl.innerHTML = slice.map(renderCard).join('');
    renderPagination(safePage, totalPages);
  }

  fetch('data/diary.json', { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('diary.json load failed');
      return res.json();
    })
    .then(function (data) {
      // 投稿日（手動入力）の新しい順
      const posts = sortPostsByDate(data.posts || []);
      if (!posts.length) {
        showEmpty('まだ投稿がありません。');
        return;
      }
      renderPage(posts, getPageNumber());
    })
    .catch(function () {
      showEmpty('ブログを読み込めませんでした。');
    });
})();
