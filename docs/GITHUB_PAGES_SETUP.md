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

1. `main` にこのリポジトリの最新を push する
2. GitHub → **Settings** → **Pages**
3. **Build and deployment** → **Source**: **GitHub Actions**（Deploy from a branch ではない）
4. **Actions** → **Deploy GitHub Pages** が成功するまで待つ（初回 2〜5 分）
5. 上記 URL で表示確認

以前 **gh-pages ブランチ** で公開していた場合は、Pages の Source を **GitHub Actions** に切り替えてください（`gh-pages` ブランチは使いません）。

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
