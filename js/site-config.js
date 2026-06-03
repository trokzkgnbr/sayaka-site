/** サイト共通設定（文言・画像パスはここで差し替え） */
window.SITE = {
  artistNameJa: '羊水サヤ',
  artistNameEn: 'SAYA YOSUI',
  role: '作詞家 / 油絵作家',
  email: 'pikinsaya@gmail.com',
  mailSubject: 'Portfolio サイトからのお問い合わせ',

  /** トップ画像下のキャプション（右詰め） */
  homeCaption: {
    year: '2022',
    title: '今日からあなたは私だけの夢を見る',
    poem: [
      '美しくて醜い魂が零れる滴のように',
      'いつしか蝶と呼ばれて',
      '天に還る',
    ],
    medium: 'oil on canvas',
    size: '1303 × 1940mm',
  },

  profileShort:
    '言葉と色彩の両方で表現する。歌のための詞を書き、油彩でキャンバスに景色や静物を重ねる。音と絵画のあいだにある感覚を、作品として残しています。',

  profileLong: `
    <p>プロフィールの詳細文をここに記載します。経歴、制作スタイル、使用ツール、受賞歴など、About ページ向けの長めのテキストを入れてください。</p>
    <p>第二段落として、代表作や展示・上映歴、メディア掲載などを箇条書きや段落で追記できます。</p>
    <h3>主な活動</h3>
    <ul>
      <li>作詞（楽曲提供・リリック制作）</li>
      <li>油彩による風景・静物・人物の制作</li>
      <li>個展・グループ展への出品</li>
    </ul>
  `.trim(),

  homeVisual: 'images/home/main-visual.jpg',

  /** ヘッダー右上 SNS（@pikinsaya）。Blog 同期元は @4mnion → config/instagram.env */
  sns: {
    instagram: 'https://www.instagram.com/pikinsaya/',
    x: 'https://x.com/pikinsaya',
  },

  nav: [
    { id: 'home', label: 'Home', href: 'index.html' },
    { id: 'gallery', label: 'Gallery', href: 'gallery-dawn.html' },
    { id: 'about', label: 'Profile', href: 'about.html' },
    { id: 'diary', label: 'Blog', href: 'diary.html' },
    { id: 'contact', label: 'Contact', href: 'contact.html' },
  ],

  /** Gallery サブカテゴリ（ホバーで表示・各ページへ） */
  galleryCategories: [
    {
      slug: 'dawn',
      label: 'そして夜明けを拒むでしょう',
      href: 'gallery-dawn.html',
    },
    {
      slug: 'dream',
      label: 'Walk in a dream',
      href: 'gallery-dream.html',
    },
    {
      slug: 'colors',
      label: '色彩の余白',
      href: 'gallery-colors.html',
    },
  ],

  flowWords: [
    'LYRICS',
    'OIL PAINTING',
    'CANVAS',
    'SONG',
    'COLOR',
    'ART',
  ],
};
