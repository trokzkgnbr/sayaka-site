/** サイト共通設定（文言・画像パスはここで差し替え） */
window.SITE = {
  /** CSS/JS の ?v= と揃える（更新時は HTML の ?v= も同じ番号に） */
  assetVersion: '22',
  artistNameJa: '羊水サヤ',
  artistNameEn: 'Saya Yosui',
  role: '油絵作家 / 作詞家',
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

  profileLong: `
    <div class="profile-bio">
      <p>1999　愛知県に生まれる</p>
      <p>2022　武蔵野美術大学 卒業</p>
      <p>2025　公益財団法人かすがい市民文化財団<br>　　　みんなの美術部　美術部サポーター</p>
    </div>

    <h2 class="profile-section-title">statement</h2>
    <p>小さな幸せ 小さな愛を届ける<br>わたしの役目です.</p>
    <p>わたしにとって絵を描くということは<br>人が神に祈りを捧げるということと似ているのかもしれません.</p>
    <p>ひとは本能的に1番大事にしてしまっているものがそれぞれありますが<br>わたしは圧倒的に美しさを1番大事に思っています.<br>美しいということも人それぞれのカタチがあるでしょう.</p>
    <p>自分が持つ美しさを常に探求し<br>息ができない程の美しさを産み出すために絵を描き<br>また 絵を描くという表現以外でも創造し<br>太陽の光に幸せを感じながら 水が流れるように愛を与えながら<br>日々を過ごしています.</p>

    <h2 class="profile-section-title">Selected group exhibitions / Prize</h2>
    <ul class="profile-cv">
      <li>2017　第41回 全国高等学校総合文化祭みやぎ総文 2017美術･工芸部門 愛知県代表</li>
      <li>2018　jica独立行政法人 国際協力機構 CM作画協力</li>
      <li>2019　武蔵野美術大学 2年進級制作展 遠藤彰子賞<br>　　　グループ展「無添加」(Space WAIZE / Tokyo)<br>　　　グループ展「ふゆやすみ」(alt_medium / Tokyo)</li>
      <li>2020　武蔵野美術大学 コンクール 竹内一賞</li>
      <li>2021　武蔵野美術大学 卒業制作 優秀賞<br>　　　グループ展「Path展」(Gallery Art Point / Tokyo)</li>
      <li>2025　世界絵画大賞展 ミューズ賞</li>
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
    { id: 'gallery', label: 'Gallery', href: 'gallery.html?category=dawn' },
    { id: 'about', label: 'profile', href: 'about.html' },
    { id: 'diary', label: 'blog', href: 'diary.html' },
    { id: 'contact', label: 'Contact', href: 'contact.html' },
  ],

  /** Gallery サブカテゴリ（ホバーで表示・各ページへ） */
  galleryCategories: [
    {
      slug: 'dawn',
      label: 'そして夜明けを拒むでしょう',
      href: 'gallery.html?category=dawn',
    },
    {
      slug: 'fragments',
      label: 'fragments',
      href: 'gallery.html?category=fragments',
    },
    {
      slug: 'dream',
      label: 'walk in a dream',
      href: 'gallery.html?category=dream',
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
