# 外出先から Blog 管理する

更新日: 2026-06-16 JST

## 方針

- 管理画面 URL … **https://sayayosui.site/blog-mgt-bf8fa662/**（サイト配下・リンクは載せない）
- パスワード … **サーバー側だけ**（HTML / CSS / JS に平文は入れない）
- それ以上のセキュリティ（Render 等）は **不要**

## 重要: GitHub Pages だけでは投稿できない

Pages に載るのは **画面（HTML/CSS/JS）だけ** です。  
ログイン・画像アップロード・保存には **API サーバー** が必要です。

| 場所 | URL | 投稿・削除 |
|------|-----|-----------|
| 公開サイト | https://sayayosui.site/blog-mgt-bf8fa662/ | 画面のみ（API なし） |
| 自宅 Mac | http://127.0.0.1:8765/blog-mgt-bf8fa662/ | **使える** |

## 外出先から使う（Render 不要）

**Mac を起動した状態**で、次のどちらか。

### A. 同じ Wi‑Fi 内（簡単）

1. `config/admin.env` で `ADMIN_BIND=0.0.0.0` に変更
2. `bash scripts/run_diary_admin.sh`
3. Mac の LAN IP で開く（例 `http://192.168.1.10:8765/blog-mgt-bf8fa662/`）

### B. 外出先（Tailscale など・無料）

1. Mac とスマホに Tailscale を入れる
2. いつもどおり `run_diary_admin.sh`（`127.0.0.1` のままで OK）
3. スマホから Mac の Tailscale IP で `http://100.x.x.x:8765/blog-mgt-bf8fa662/`

→ **sayayosui.site の URL そのもの**で編集したい場合は、Cloudflare 等で API を同じドメインに載せる別途設定が要ります（通常は A/B で十分）。

## 秘密パスを変える

`config/blog-admin-path.txt` の1行と、`config/admin.env` の `ADMIN_PATH` を **同じ値** に揃える。

## 本番 Blog への反映

`GITHUB_TOKEN` を `config/admin.env` に入れている場合 … 投稿・削除後 **自動 push**  
未設定の場合 … 従来どおり `git add data/diary.json images/diary/` → push

## Render について

**必須ではありません。** 常時オン・Mac なしで使いたい場合だけ選択肢のひとつです。
