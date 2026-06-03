const SNS_SVG = {
  instagram: `<svg class="site-sns__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="4" y="4" width="16" height="16" rx="4.5"/><circle cx="12" cy="12" r="3.75"/><circle cx="17.2" cy="6.8" r="0.9" fill="currentColor" stroke="none"/></svg>`,
  x: `<svg class="site-sns__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.35" stroke-linecap="round" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18"/></svg>`,
};

const SNS_LABELS = {
  instagram: 'Instagram',
  x: 'X（旧Twitter）',
};

function renderSns() {
  const root = document.getElementById('site-sns');
  const urls = window.SITE?.sns;
  if (!root || !urls) return;

  const fragment = document.createDocumentFragment();

  for (const [key, url] of Object.entries(urls)) {
    const a = document.createElement('a');
    a.className = 'site-sns__link';
    a.href = url || '#';
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.setAttribute('data-sns', key);
    a.setAttribute('aria-label', SNS_LABELS[key] || key);
    a.innerHTML = SNS_SVG[key] || '';
    fragment.appendChild(a);
  }

  root.replaceChildren(fragment);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', renderSns);
} else {
  renderSns();
}
