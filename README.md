# Portfolio Site（マルチページ）

更新日: 2026-06-01 JST

[imoredy.com](https://www.imoredy.com/) を参考にした静的ポートフォリオ。**ページごとに HTML を分割**。

## ページ構成

| ファイル | 内容 |
|----------|------|
| `index.html` | Home — 作家名（上）→ メインビジュアル（油彩画像）→ 短いプロフィール |
| `about.html` | About — 詳細プロフィール |
| `gallery.html` | Gallery — 作品画像の一覧 |
| `diary.html` | Diary — 一覧（画像・先頭行・日付） |
| `diary-post.html` | Diary — 詳細（`?id=`） |
| `data/diary.json` | Diary 投稿データ（サンプル） |
| `contact.html` | Contact — フォーム送信で mailto 起動（Gmail / メールアプリ） |

## Diary（Instagram 連携）

- 一覧: `diary.html` — サムネ・タイトル（先頭行）・投稿日。
- 詳細: `diary-post.html?id=...` — 全文・画像1枚（正方形想定）。
- データ正本: `data/diary.json` + `images/diary/*.jpg`
- **セットアップ（非エンジニア向け）:** [`docs/INSTAGRAM_DIARY_SETUP.md`](docs/INSTAGRAM_DIARY_SETUP.md)
- **渡す前チェック:** [`docs/HANDOFF_WHEN_READY.md`](docs/HANDOFF_WHEN_READY.md)
- 手動同期: `bash scripts/run_sync.sh`（`config/instagram.env` 要）
- 自動同期: `.github/workflows/sync-instagram-diary.yml`（GitHub Secrets 設定後、**12:00・24:00 JST** にクラウド実行）

## ローカル表示

```bash
cd ~/.openclaw/workspace/40_work/portfolio_site
python3 -m http.server 8080
# http://localhost:8080/index.html
```

`portfolio_site` フォルダだけ渡して相手が同じコマンドを実行してもよい（`file://` で開くと一部の挙動が不安定になりやすい）。

## 他の人に URL で見せる（おすすめ順）

いずれも **HTML/CSS/JS だけ**の静的サイト向け。公開するのは `portfolio_site` フォルダ全体（`index.html` が直下にある状態）。

### 1. Netlify Drop（いちばん手軽・GUI）

**用意済み ZIP（ルートに `index.html` がある構成）:**

`40_work/portfolio_site-netlify-drop.zip`

**手順（約2分）**

1. ブラウザで <https://app.netlify.com/drop> を開く
2. 初回だけ **Netlify 無料アカウント**（メール / Google / GitHub のいずれか）でログイン
3. 上記 ZIP をドロップ（または `portfolio_site` フォルダごとドロップでも可）
4. 表示された `https://ランダム名.netlify.app` を共有

**あとから:** Site configuration → Site name で `saya-yosui` などにすると `https://saya-yosui.netlify.app` に変更できる。

**更新:** 同じ ZIP を再度 Drop するか、ダッシュボードの Deploys から再アップロード。

**ZIP の再生成:**

```bash
cd ~/.openclaw/workspace/40_work/portfolio_site
zip -r ../portfolio_site-netlify-drop.zip . -x "*.DS_Store" -x "README.md"
```

### 2. Surge（ターミナル1コマンド）

```bash
cd ~/.openclaw/workspace/40_work/portfolio_site
npx surge . saya-yosui.surge.sh
```

初回はメール登録のみ。表示された URL をそのまま共有できる。

### 3. Cloudflare Pages / Vercel（無料・Git 連携向け）

GitHub に `portfolio_site` だけのリポジトリを置き、Cloudflare Pages または Vercel で「ルート = そのリポジトリ」を選ぶと、push のたびに自動更新される。

いまのワークスペース全体（`terako`）のままだとパスが深いので、**ポートフォリオ専用リポジトリ**にするか、Deploy 時の公開ディレクトリを `40_work/portfolio_site` に指定する。

### 4. GitHub Pages（本番・推奨）

リポジトリ `trokzkgnbr/sayaka-site` では **Actions が自動デプロイ** します。

- 手順・URL: [`docs/GITHUB_PAGES_SETUP.md`](docs/GITHUB_PAGES_SETUP.md)
- 公開 URL: https://trokzkgnbr.github.io/sayaka-site/
- `main` に push（Blog 同期のコミット含む）→ 数分で本番更新
- Netlify 無料のデプロイクレジットを使わずに Git と本番を揃えやすい

---

**注意**

- `js/site-config.js` — メール・SNS（@pikinsaya）。Diary 同期は **@4mnion**（`docs/INSTAGRAM_DIARY_SETUP.md`）
- 画像はリポジトリに含める（外部だけだとリンク切れに注意）
- Contact は相手の Gmail / メールアプリが開く仕様のまま（サーバー送信はしない）

## カスタマイズ（正本: `js/site-config.js`）

- 作家名・役割・プロフィール短文/長文・送信先メール（`email`・画面には非表示）
- Home 画像: `images/home/main-visual.jpg`（`homeVisual`）
- ギャラリー: `images/gallery/` + `js/gallery.js` の `GALLERY_ITEMS`

## Contact の動き

「送信」で **Gmail の作成画面**（新しいタブ）を開く。`メールアプリで開く` は `mailto:` 用。サーバー送信は行わない。

**Contact:** 送信先は `site-config.js` の `email`（`pikinsaya@gmail.com`）。

**SNS:** ヘッダーは `sns`（Instagram / X → @pikinsaya）。Diary 投稿の取得元は @4mnion。
