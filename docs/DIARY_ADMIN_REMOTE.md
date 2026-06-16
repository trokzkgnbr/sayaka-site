# 外出先から Blog 管理する

更新日: 2026-06-16 JST

## 考え方

- **公開サイト** … https://sayayosui.site/（閲覧用）
- **管理画面** … 別 URL・**推測されにくいパス** + **パスワード**
- 公開サイトには管理画面へのリンクを **載せない**
- 投稿・削除後は **GitHub へ自動 push** → 数分で本番反映

パスワードが分からなければ中身は見えませんが、HTTPS と秘密 URL の両方で守る想定です。  
アクセス数が少ないサイト向けの現実的なラインです。

## 1. 秘密パスを決める

```bash
bash scripts/generate_admin_path.sh
```

表示された `blog-mgt-xxxxxxxx` をメモ（**他人に教えない**）。

## 2. GitHub トークン（PAT）

1. GitHub → Settings → Developer settings → Personal access tokens
2. **repo** 権限付きトークンを作成
3. Render の環境変数 `GITHUB_TOKEN` に貼る

## 3. Render でデプロイ

1. https://render.com で GitHub 連携
2. リポジトリ `trokzkgnbr/sayaka-site` を選択
3. **Blueprint** または Web Service で `render.yaml` を使用
4. 環境変数を追加:

| 変数 | 値 |
|------|-----|
| `ADMIN_PATH` | 手順1で生成した文字列 |
| `ADMIN_PASSWORD_HASH` | 下記コマンドで生成 |
| `SESSION_SECRET` | 下記コマンドで生成 |
| `GITHUB_TOKEN` | 手順2の PAT |
| `ADMIN_PUBLIC_URL` | デプロイ後の URL（例 `https://sayaka-blog-admin.onrender.com`） |

パスワードハッシュ生成（例: パスワード `hogege00i`）:

```bash
python3 scripts/setup_admin_password.py --password-stdin <<<"あなたのパスワード"
grep -E '^(ADMIN_PASSWORD_HASH|SESSION_SECRET)=' config/admin.env
```

`config/admin.env` の2行を Render にコピー。

5. Deploy

## 4. 管理画面 URL

```
https://<Render のホスト名>/<ADMIN_PATH>/
```

例:

```
https://sayaka-blog-admin.onrender.com/blog-mgt-a1b2c3d4/
```

スマホのブラウザに **ブックマーク** してください。

## 5. ローカルとの違い

| | ローカル | 外出先（Render） |
|--|---------|-----------------|
| 起動 | `bash scripts/run_diary_admin.sh` | 常時オン |
| URL | http://127.0.0.1:8765/admin/ | 秘密 URL |
| 本番反映 | 手動 push も可 | 自動 push |

ローカルでも `GITHUB_TOKEN` を `config/admin.env` に入れると自動 push できます。

## 注意

- `ADMIN_PATH` を `/admin` のままにしない（推測されやすい）
- Render 無料枠は **15分無操作でスリープ** → 初回アクセスが遅いことがあります
- PAT は GitHub Secrets 管理画面以外に保存しない
