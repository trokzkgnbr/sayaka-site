# GitHub Pages セットアップ（本番サイト）

更新日: 2026-06-05 JST

リポジトリ: `trokzkgnbr/sayaka-site`  
公開 URL: **https://trokzkgnbr.github.io/sayaka-site/**

## 何が自動で動くか

| 処理 | ワークフロー | タイミング |
|------|--------------|------------|
| Instagram → Blog データ | `Sync Instagram Diary` | 毎日 12:05・24:05 JST 頃 + 手動 |
| サイト公開 | `Deploy GitHub Pages` | `main` で公開対象ファイルが変わった push + 手動 |

Blog 同期が `data/diary.json` を更新して push すると、続けて **Deploy** が走り本番に反映されます。

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

## Blog が古く見えるとき

1. **Sync Instagram Diary** の成否
2. **Deploy GitHub Pages** の成否
3. ブラウザのスーパーリロード

## 公開されないファイル

`scripts/prepare-pages-site.sh` により配信しないもの: `scripts/`, `docs/`, `config/`, `.github/`, `README.md`
