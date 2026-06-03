function getFormPayload(form) {
  const data = new FormData(form);
  const name = String(data.get('name') || '').trim();
  const email = String(data.get('email') || '').trim();
  const message = String(data.get('message') || '').trim();
  return { name, email, message };
}

function buildMessageBody({ name, email, message }) {
  return [
    message,
    '',
    '---',
    name ? `お名前: ${name}` : '',
    email ? `返信先メール: ${email}` : '',
  ]
    .filter(Boolean)
    .join('\n');
}

function buildMailtoUrl(to, subject, body) {
  const qs = new URLSearchParams();
  qs.set('subject', subject);
  qs.set('body', body);
  return `mailto:${to}?${qs.toString()}`;
}

/** Gmail ブラウザ版の作成画面（mailto ハンドラ不要） */
function buildGmailComposeUrl(to, subject, body) {
  const qs = new URLSearchParams({
    view: 'cm',
    fs: '1',
    to,
    su: subject,
    body,
  });
  return `https://mail.google.com/mail/?${qs.toString()}`;
}

function openUrl(url) {
  const a = document.createElement('a');
  a.href = url;
  a.rel = 'noopener noreferrer';
  if (url.startsWith('https://')) {
    a.target = '_blank';
  }
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function initContactForm() {
  const form = document.getElementById('contact-form');
  const mailtoBtn = document.getElementById('contact-mailto');
  if (!form || !window.SITE) return;

  function composeUrls() {
    const { name, email, message } = getFormPayload(form);
    if (!message) return null;
    const body = buildMessageBody({ name, email, message });
    const subject = SITE.mailSubject;
    const to = SITE.email;
    return {
      gmail: buildGmailComposeUrl(to, subject, body),
      mailto: buildMailtoUrl(to, subject, body),
    };
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const { message } = getFormPayload(form);
    if (!message) {
      form.querySelector('[name="message"]')?.focus();
      return;
    }
    const urls = composeUrls();
    if (!urls) return;
    openUrl(urls.gmail);
  });

  mailtoBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    const urls = composeUrls();
    if (!urls) {
      form.querySelector('[name="message"]')?.focus();
      return;
    }
    openUrl(urls.mailto);
  });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initContactForm);
} else {
  initContactForm();
}
