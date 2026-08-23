# スマホから Blog 更新（Mac 不要）

更新日: 2026-08-24 JST

## 全体の流れ

```
スマホ → https://sayayosui.site/blog-mgt-bf8fa662/
      → Cloudflare Worker（API・パスワード・GitHub push）
      → GitHub main 更新
      → Deploy ワークフロー（push 時 + 1日2回 9:00/21:00 JST）
      → https://sayayosui.site/ に反映
```

## 前提

- ドメイン **sayayosui.site** の DNS が **Cloudflare** 経由
- GitHub リポジトリ `trokzkgnbr/sayaka-site`

## 1. GitHub PAT（投稿の自動 push 用）

**ここが「1か月後に投稿できなくなる」最大の原因です。**

1. GitHub → Settings → Developer settings → Personal access tokens
2. Fine-grained または classic で **repo 内容の読み書き** ができるトークンを作成
3. **Expiration は 30 日（デフォルト）にしない。**  
   - 推奨: **No expiration**（無期限）  
   - または最大（366 日）にして、期限の1ヶ月前にカレンダー通知を入れる
4. 未使用のトークンは **1年で GitHub が自動失効**します。定期投稿していれば通常は問題ありません
5. `config/admin.env` に追加:

```
GITHUB_TOKEN=ghp_...
```

期限が切れた場合の症状: サイトは見られるが、管理画面からの投稿・削除だけ失敗する。  
管理画面トップに警告が出ます。新しいトークンを発行し、Cloudflare の `GITHUB_TOKEN` secret を更新してください。

## 2. Cloudflare Worker をデプロイ

```bash
cd sayaka-portfolio
npm install -g wrangler   # または npx wrangler
wrangler login
python3 scripts/setup_cloudflare_admin_api.py
# 表示された wrangler secret put ... を実行
npx wrangler deploy
```

Secrets（Cloudflare）:

| 名前 | 値 |
|------|-----|
| `ADMIN_PASSWORD_HASH` | `config/admin.env` の行 |
| `SESSION_SECRET` | 同上 |
| `GITHUB_TOKEN` | 手順1の PAT |

## 3. GitHub Pages を更新

```bash
git push origin main
```

管理 UI は `https://sayayosui.site/blog-mgt-bf8fa662/` に載ります。

## 使い方

1. スマホで上記 URL をブックマーク（公開サイトにはリンクを載せない）
2. パスワードでログイン
3. 投稿を登録 / 削除
4. 数分以内（または次の 9:00 / 21:00 JST チェック）で本番 Blog に反映

## ローカル Mac について

**不要です。** 開発・テスト用に `bash scripts/run_diary_admin.sh` は使えますが、日常更新はスマホだけで OK です。

## トラブル

| 症状 | 対処 |
|------|------|
| ログインで「管理 API が未設定」 | Worker 未デプロイ → 手順2 |
| 投稿で「GITHUB_TOKEN が未設定」 | Worker の secret を確認 |
| 投稿が突然できなくなった | PAT の期限切れ → 手順1で再発行し secret を更新 |
| 画像が Blog に載らない | Deploy ワークフロー完了を待つ（Actions タブ） |
