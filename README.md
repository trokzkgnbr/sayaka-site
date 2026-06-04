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
- 自動同期: `.github/workflows/sync-instagram-diary.yml`（GitHub Secrets 設定後、**12:05・24:05 JST 頃** + 手動）

## ローカル表示

```bash
cd ~/.openclaw/workspace/40_work/portfolio_site
python3 -m http.server 8080
# http://localhost:8080/index.html
```

`portfolio_site` フォルダだけ渡して相手が同じコマンドを実行してもよい（`file://` で開くと一部の挙動が不安定になりやすい）。

## 本番公開（GitHub Pages）

リポジトリ `trokzkgnbr/sayaka-site` を **GitHub Actions** で公開します。

- 手順: [`docs/GITHUB_PAGES_SETUP.md`](docs/GITHUB_PAGES_SETUP.md)
- URL: https://trokzkgnbr.github.io/sayaka-site/
- サイト更新: `main` へ push → **Deploy GitHub Pages** が数分以内に反映
- Blog データ: **Sync Instagram Diary**（毎日 12:05・24:05 JST 頃 + 手動）

---

**注意**

- `js/site-config.js` — メール・SNS（@pikinsaya）。Diary 同期は **@4mnion**（`docs/INSTAGRAM_DIARY_SETUP.md`）
- 画像はリポジトリに含める（外部だけだとリンク切れに注意）
- Contact は相手の Gmail / メールアプリが開く仕様のまま（サーバー送信はしない）

## カスタマイズ（正本: `js/site-config.js`）

- 作家名・役割・プロフィール短文/長文・送信先メール（`email`・画面には非表示）
- Home 画像: `images/home/main-visual.jpg`（`homeVisual`）
- ギャラリー: `images/gallery/` + `data/gallery-*.json`（表示は `js/gallery.js`）
- キャッシュ更新: `js/site-config.js` の `assetVersion` と各 HTML の `?v=` を同じ番号に

## Contact の動き

「送信」で **Gmail の作成画面**（新しいタブ）を開く。`メールアプリで開く` は `mailto:` 用。サーバー送信は行わない。

**Contact:** 送信先は `site-config.js` の `email`（`pikinsaya@gmail.com`）。

**SNS:** ヘッダーは `sns`（Instagram / X → @pikinsaya）。Diary 投稿の取得元は @4mnion。
