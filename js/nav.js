(function () {
  function bindGalleryDropdown(wrap) {
    function open() {
      wrap.classList.add('is-open');
    }
    function close() {
      wrap.classList.remove('is-open');
    }

    wrap.addEventListener('mouseenter', open);
    wrap.addEventListener('mouseleave', close);
    wrap.addEventListener('focusin', open);
    wrap.addEventListener('focusout', function (e) {
      if (!wrap.contains(e.relatedTarget)) close();
    });
  }

  function initSiteNav() {
    var nav = document.getElementById('site-nav');
    if (!nav || !window.SITE || !SITE.nav) return;

    var page = document.body.getAttribute('data-page') || '';
    var galleryCategory = document.body.getAttribute('data-gallery-category') || '';
    var items = SITE.nav;
    var categories = SITE.galleryCategories || [];
    var fragment = document.createDocumentFragment();

    items.forEach(function (item) {
      if (item.id === 'gallery' && categories.length) {
        var wrap = document.createElement('div');
        wrap.className = 'site-nav__item site-nav__item--dropdown';

        var isGallerySection = page === 'gallery' || galleryCategory;
        var mainHref = categories[0].href;

        var mainLink = document.createElement('a');
        mainLink.className =
          'site-nav__link' + (isGallerySection && !galleryCategory ? ' is-active' : '');
        if (isGallerySection && !galleryCategory) {
          mainLink.setAttribute('aria-current', 'page');
        }
        mainLink.href = mainHref;
        mainLink.textContent = item.label;
        wrap.appendChild(mainLink);

        var sub = document.createElement('ul');
        sub.className = 'site-nav__submenu site-nav__submenu--row';
        sub.setAttribute('role', 'menu');
        sub.setAttribute('aria-label', item.label + ' categories');

        categories.forEach(function (cat) {
          var li = document.createElement('li');
          li.setAttribute('role', 'none');
          var subLink = document.createElement('a');
          subLink.className = 'site-nav__submenu-link';
          subLink.href = cat.href;
          subLink.textContent = cat.label;
          subLink.setAttribute('role', 'menuitem');
          if (galleryCategory === cat.slug) {
            subLink.classList.add('is-active');
            subLink.setAttribute('aria-current', 'page');
            mainLink.classList.add('is-active');
            mainLink.setAttribute('aria-current', 'page');
          }
          li.appendChild(subLink);
          sub.appendChild(li);
        });

        wrap.appendChild(sub);
        bindGalleryDropdown(wrap);
        fragment.appendChild(wrap);
        return;
      }

      var link = document.createElement('a');
      link.className = 'site-nav__link';
      link.href = item.href;
      link.textContent = item.label;

      var isActive =
        (item.id === 'home' && page === 'home') ||
        (item.id === 'about' && page === 'about') ||
        (item.id === 'diary' && (page === 'diary' || page === 'diary-post')) ||
        (item.id === 'contact' && page === 'contact');

      if (isActive) {
        link.classList.add('is-active');
        link.setAttribute('aria-current', 'page');
      }

      fragment.appendChild(link);
    });

    nav.replaceChildren(fragment);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSiteNav);
  } else {
    initSiteNav();
  }
})();
