function initAboutContent() {
  const root = document.getElementById('about-content');
  if (!root || !window.SITE) return;
  root.innerHTML = SITE.profileLong;

  const nameJa = document.getElementById('about-name-ja');
  const nameEn = document.getElementById('about-name-en');
  const role = document.getElementById('about-role');
  if (nameJa) nameJa.textContent = SITE.artistNameJa;
  if (nameEn) nameEn.textContent = SITE.artistNameEn;
  if (role) role.textContent = SITE.role;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAboutContent);
} else {
  initAboutContent();
}
