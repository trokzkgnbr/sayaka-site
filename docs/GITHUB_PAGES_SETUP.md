# GitHub Pages セットアップ（本番サイト）

更新日: 2026-06-05 JST

リポジトリ: `trokzkgnbr/sayaka-site`  
公開 URL（初期）: **https://trokzkgnbr.github.io/sayaka-site/**

## 何が自動で動くか

| 処理 | ワークフロー | タイミング |
|------|--------------|------------|
| Instagram → Blog データ | `Sync Instagram Diary` | 毎日 12:05・24:05 JST 頃 + `main` への push + 手動 |
| サイト公開 | `Deploy GitHub Pages` | `main` で HTML/CSS/JS/画像/data が変わった push + 手動 |

Blog 同期が `data/diary.json` を更新して push すると、続けて **Deploy** が走り、本番に反映されます。

## 初回だけ（リポジトリ管理者）

1. GitHub → **Settings** → **Pages**
2. **Build and deployment** → **Source**: **Deploy from a branch**
3. **Branch**: `gh-pages` / **/(root)** を選んで **Save**  
   （まだ `gh-pages` が無い場合は、次の手順 4 の Actions 成功後にもう一度開く）
4. GitHub → **Actions** → **Deploy GitHub Pages** が緑になるまで待つ（初回 2〜5 分）
5. **https://trokzkgnbr.github.io/sayaka-site/** を開いて表示確認
6. （任意）独自ドメイン: **Pages** → **Custom domain** で設定し、DNS を向ける

## Netlify から移す場合

- いまの `sayayosui.netlify.app` は、移行確認が終わるまで残しておいてもよい
- 独自ドメインを Netlify で使っている場合は、DNS を **GitHub Pages の案内**に合わせて切り替える
- Netlify の GitHub 連携はオフにすると、二重デプロイとクレジット消費を防げる

## Blog が古く見えるとき

1. **Actions** → **Sync Instagram Diary** が成功しているか
2. 続けて **Deploy GitHub Pages** が成功しているか
3. ブラウザのスーパーリロード（`diary.json` は `cache: 'no-store'` で取得）

## 公開されないファイル

`scripts/prepare-pages-site.sh` により、次は **サイトに載せません**（リポジトリには残る）:

- `scripts/`, `docs/`, `config/`
- `.github/`, `README.md`, `netlify.toml`
