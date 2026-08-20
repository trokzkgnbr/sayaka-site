/** サイト共通設定（文言・画像パスはここで差し替え） */
window.SITE = {
  /** ブラウザタブタイトル（SAYAYOSUI｜home 形式） */
  siteBrand: 'SAYAYOSUI',
  pageTitle: function (pageName) {
    return this.siteBrand + '｜' + pageName;
  },

  /** CSS/JS の ?v= と揃える（更新時は HTML の ?v= も同じ番号に） */
  assetVersion: '61',
  artistNameJa: '羊水サヤ',
  artistNameEn: 'Saya Yosui',
  /** ヘッダーロゴ */
  logo: 'images/logo.png',
  logoWidth: 1024,
  logoHeight: 187,
  role: '油絵作家 / 作詞家',
  email: 'pikinsaya@gmail.com',
  mailSubject: 'Portfolio サイトからのお問い合わせ',

  /** トップ画像下のキャプション（右詰め） */
  homeCaption: {
    year: '2022',
    title: '今日からあなたはわたしの夢だけをみる',
    poem: [
      '美しくて醜い魂が零れる滴のように',
      'いつしか蝶に呼ばれて',
      '天に還る',
    ],
    medium: 'oil on canvas',
    size: '1303 × 1940mm',
  },

  profileLong: `
    <div class="profile-bio">
      <p class="profile-line"><span class="profile-year">1999</span><span class="profile-line__text">愛知県に生まれる</span></p>
      <p class="profile-line"><span class="profile-year">2022</span><span class="profile-line__text">武蔵野美術大学 卒業</span></p>
      <p class="profile-line"><span class="profile-year">2025</span><span class="profile-line__text">公益財団法人かすがい市民文化財団</span></p>
      <p class="profile-line"><span class="profile-year" aria-hidden="true"></span><span class="profile-line__text">みんなの美術部　美術部サポーター</span></p>
    </div>

    <h2 class="profile-section-title">statement</h2>
    <p>小さな幸せ 小さな愛を届ける<br>わたしの役目です.</p>
    <p>わたしにとって絵を描くということは<br>人が神に祈りを捧げるということと<br>似ているのかもしれません.</p>
    <p>ひとは本能的に<br>1番大事にしてしまっているものがそれぞれありますが<br>わたしは圧倒的に美しさを1番大事に思っています.<br>美しいということも人それぞれのカタチがあるでしょう.</p>
    <p>自分が持つ美しさを常に探求し<br>息ができない程の美しさを産み出すために絵を描き<br>また 絵を描くという表現以外でも創造し<br>太陽の光に幸せを感じながら<br>水が流れるように愛を与えながら<br>日々を過ごしています.</p>

    <h2 class="profile-section-title">Selected group exhibitions / Prize</h2>
    <ul class="profile-cv">
      <li class="profile-line"><span class="profile-year">2017</span><span class="profile-line__text">第41回 全国高等学校総合文化祭みやぎ総文 2017美術･工芸部門 愛知県代表</span></li>
      <li class="profile-line"><span class="profile-year">2018</span><span class="profile-line__text">jica独立行政法人 国際協力機構 CM作画協力</span></li>
      <li class="profile-line">
        <span class="profile-year">2019</span>
        <span class="profile-line__text">武蔵野美術大学 2年進級制作展 遠藤彰子賞<br><span class="profile-line__sub">グループ展「無添加」(Space WAIZE / Tokyo)</span><span class="profile-line__sub">グループ展「ふゆやすみ」(alt_medium / Tokyo)</span></span>
      </li>
      <li class="profile-line"><span class="profile-year">2020</span><span class="profile-line__text">武蔵野美術大学 コンクール 竹内一賞</span></li>
      <li class="profile-line">
        <span class="profile-year">2021</span>
        <span class="profile-line__text">武蔵野美術大学 卒業制作 優秀賞<br><span class="profile-line__sub">グループ展「Path展」(Gallery Art Point / Tokyo)</span></span>
      </li>
      <li class="profile-line"><span class="profile-year">2025</span><span class="profile-line__text">世界絵画大賞展 ミューズ賞</span></li>
    </ul>
  `.trim(),

  homeVisual: 'images/home/main-visual.jpg',

  /** ヘッダー右上 SNS（@pikinsaya） */
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
