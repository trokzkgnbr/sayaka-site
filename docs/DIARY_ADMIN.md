# Blog 管理（非公開）

更新日: 2026-06-16 JST

## スマホから更新（通常）

**[ADMIN_PHONE.md](./ADMIN_PHONE.md)** — Mac 不要。  
`https://sayayosui.site/blog-mgt-bf8fa662/` から投稿 → GitHub → 本番サイトへ自動反映。

## ローカル Mac（開発・テスト用）

```bash
bash scripts/run_diary_admin.sh
# http://127.0.0.1:8765/blog-mgt-bf8fa662/
```

## 初回セットアップ（1回）

```bash
bash scripts/setup_admin_password.sh
# またはブラウザの setup.html（ローカルサーバー起動時）
```

パスワードは `config/admin.env` に **ハッシュだけ** 保存（平文は Git に入れない）。

## 画面

| URL | 用途 |
|-----|------|
| `/blog-mgt-bf8fa662/login.html` | ログイン |
| `/blog-mgt-bf8fa662/` | トップ |
| `/blog-mgt-bf8fa662/register.html` | 投稿登録 |
| `/blog-mgt-bf8fa662/delete.html` | 投稿削除 |

## 本番への反映

1. 投稿・削除 → Cloudflare Worker が GitHub の `main` を更新
2. **push 直後** に Deploy ワークフローが走る
3. **1日2回（9:00 / 21:00 JST）** も差分チェックしてデプロイ（取りこぼし防止）

公開 Blog: https://sayayosui.site/

## セキュリティ

| 項目 | 内容 |
|------|------|
| パスワード | 平文は保存しない（Worker / admin.env にハッシュのみ） |
| URL | 秘密パス `blog-mgt-bf8fa662`（サイトにリンクしない） |
| 公開 | `robots.txt` で検索除外 |

## ファイル

| パス | 意味 |
|------|------|
| `admin/` | 管理 UI |
| `workers/blog-admin-api.js` | 本番 API（Cloudflare） |
| `scripts/diary_admin_server.py` | ローカル API |
| `config/admin.env` | ローカル設定（Git 除外） |
| `config/blog-admin-path.txt` | 秘密パス |
