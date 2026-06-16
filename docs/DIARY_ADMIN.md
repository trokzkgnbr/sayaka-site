# Blog 管理（非公開）

更新日: 2026-06-16 JST

Blog（Diary）の投稿登録・削除は **ローカル管理サーバー** から行います。  
公開サイト（GitHub Pages）には管理画面は載せません。

## なぜローカルサーバーか

- **パスワードを GitHub や JavaScript に載せない**ため
- 管理 API が **あなたの PC 上だけ** で動く（既定: `127.0.0.1`）
- 他社や一般公開から **直接アクセスできない**

## 外出先から使う

秘密 URL + パスワードのみ。**Render は不要**です。  
手順: **[DIARY_ADMIN_REMOTE.md](./DIARY_ADMIN_REMOTE.md)**

## 初回セットアップ（1回）

```bash
cd sayaka-portfolio
bash scripts/setup_admin_password.sh
```

パスワードは `config/admin.env` に **ハッシュだけ** 保存されます（平文は Git に入りません）。

## 起動

```bash
bash scripts/run_diary_admin.sh
```

ブラウザで **http://127.0.0.1:8765/admin/** を開く。

## 画面

| URL | 用途 |
|-----|------|
| `/admin/login.html` | ログイン |
| `/admin/` | トップ（メニュー） |
| `/admin/register.html` | **投稿登録**（画像・日付・本文） |
| `/admin/delete.html` | **投稿削除** |

- **日付** … 空欄なら **今日（日本時間）**
- **本文** … 1行目が Blog のタイトルになる

## 本番への反映

管理サーバーは `data/diary.json` と `images/diary/` を更新します。

- **`GITHUB_TOKEN` あり** … 投稿・削除後に GitHub へ自動 push → すぐ Deploy ワークフローが走る
- **手動 push** … `git add data/diary.json images/diary/` → push
- **1日2回（9:00 / 21:00 JST）** … 変更があるか自動確認し、あれば GitHub Pages へデプロイ（取りこぼし防止）

公開 Blog: https://sayayosui.site/

## セキュリティ

| 項目 | 内容 |
|------|------|
| パスワード | PBKDF2 ハッシュのみ `config/admin.env` に保存 |
| セッション | HttpOnly Cookie（12時間） |
| 公開 | `admin/` は GitHub Pages ビルドに **含まれない** |
| ネットワーク | 既定 `127.0.0.1` のみ listen |

**注意:** `ADMIN_BIND=0.0.0.0` にすると LAN 内からアクセス可能になります。  
インターネットに直接公開しないでください（HTTPS なしの簡易認証のため）。

## ファイル

| パス | 意味 |
|------|------|
| `admin/` | 管理 UI（HTML/CSS/JS） |
| `scripts/diary_admin_server.py` | 管理 API + 認証 |
| `config/admin.env` | パスワードハッシュ（Git 除外） |
