# GitHub Pages セットアップ（本番サイト）

更新日: 2026-06-16 JST

リポジトリ: `trokzkgnbr/sayaka-site`  
公開 URL: **https://trokzkgnbr.github.io/sayaka-site/**

## 何が自動で動くか

| 処理 | ワークフロー | タイミング |
|------|--------------|------------|
| サイト公開 | `Deploy GitHub Pages` | `main` で公開対象ファイルが変わった push + 手動 |

## 初回だけ（リポジトリ管理者）

1. `main` に push する
2. GitHub → **Settings** → **Pages**
3. **Source**: **Deploy from a branch** → Branch **`gh-pages`** / **/(root)** → Save  
   （`gh-pages` がまだ無い場合は **Deploy GitHub Pages** Actions が成功してから再度開く）
4. **Actions** → **Deploy GitHub Pages** が緑になるまで待つ
5. https://trokzkgnbr.github.io/sayaka-site/ で確認

## 旧 URL

| 旧 | 新 |
|----|-----|
| `gallery-dawn.html` など | `gallery.html?category=dawn`（旧 HTML はリダイレクトのみ） |

## サイトが古く見えるとき

1. **Deploy GitHub Pages** の成否
2. ブラウザのスーパーリロード

## 公開されないファイル

`scripts/prepare-pages-site.sh` により配信しないもの: `scripts/`, `docs/`, `config/`, `admin/`, `.github/`, `README.md`
