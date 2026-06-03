# Diary × Instagram 連携セットアップ（非エンジニア向け）

更新日: 2026-06-01 JST

このサイトの **Diary ページ**は、Instagram **@4mnion** に投稿した内容を **GitHub Actions（クラウド）で1日2回自動**で取り込みます（**12:00・24:00 日本時間**）。  
（画像1枚・正方形の投稿を想定。動画・リールは取り込みません。）

※ サイト右上の Instagram / X リンク（**@pikinsaya**）とは別アカウントです。

**お金はかかりません**（Netlify 無料枠 + GitHub 無料 + Meta API 無料）。

---

## 全体の流れ（チェックリスト）

初回だけ（合計 1〜2 時間程度）:

- [ ] **A.** Instagram を「プロアカウント（ビジネス or クリエイター）」にする
- [ ] **B.** Facebook ページと Instagram を連携する
- [ ] **C.** Meta（Facebook）で開発用アプリを1つ作る
- [ ] **D.** アクセストークンを取得してメモする
- [ ] **E.** このサイトを GitHub に置く
- [ ] **F.** GitHub にトークンを登録（Secrets）
- [ ] **G.** 同期を1回テストする

初回が終われば **あとは自動** です（毎日 **12:00・24:00 JST** に GitHub 上で同期 → Netlify 連携時はサイト反映）。

---

## 必要なもの

| もの | 用途 |
|------|------|
| Instagram **@4mnion**（Diary 用・1つ） | 日記の元データ |
| Facebook アカウント | Meta 開発者用 |
| GitHub アカウント（無料） | 自動同期の実行場所 |
| Netlify アカウント（無料） | サイト公開（すでに Drop で作った場合も連携可） |

---

## A. Instagram をプロアカウントにする

1. スマホの Instagram アプリを開く  
2. **プロフィール** → **プロフィールを編集**（または設定）  
3. **アカウントの種類とツール** → **プロアカウントに切り替える**  
4. **ビジネス** または **クリエイター** を選ぶ（どちらでも可）

---

## B. Facebook ページと連携する

1. Instagram の **設定** → **アカウントの中心** → **ページをリンク**  
2. 指示に従い **Facebook ページ**を作成または既存ページとリンク  
3. リンクできていることを確認

※ ページが無いと後の API が使えません。

---

## C. Meta でアプリを作る（1回だけ）

1. ブラウザで <https://developers.facebook.com/> を開く  
2. Facebook でログイン → **マイアプリ** → **アプリを作成**  
3. 種類: **ビジネス**（または他でも可）→ 名前は例: `Portfolio Diary` → 作成  
4. 左メニュー **製品を追加** → **Instagram** → **Instagram API の設定** まで進める  
5. **アプリモード**が「開発」のときは、自分の Instagram を **Instagram テスター**として追加  
   - 左メニュー **アプリの役割** → **役割** → Instagram テスターに自分を追加  
   - スマホ Instagram の **設定 → セキュリティ → アプリとウェブサイト** で招待を承認  

（公開モードにする手順は Meta の案内に従ってください。個人サイトなら開発モード＋テスターでも動くことが多いです。）

---

## D. アクセストークンを取得する

### D-1. 短期トークン（Graph API エクスプローラ）

1. <https://developers.facebook.com/tools/explorer/> を開く  
2. 右上 **Meta アプリ** で、さきほど作ったアプリを選ぶ  
3. **ユーザートークンを取得** → 次の権限にチェック（表示名は多少異なる場合あり）  
   - `instagram_basic`  
   - `pages_show_list`  
   - `pages_read_engagement`  
4. **アクセストークンを生成** → 表示された長い文字列を **コピー**（誰にも見せない）

### D-2. 長期トークンに変換（60日程度 → 更新しやすくする）

1. <https://developers.facebook.com/tools/debug/accesstoken/> を開く  
2. D-1 のトークンを貼り付け → **デバッグ**  
3. 画面下部 **アクセストークンを延長** を押す → 新しいトークンをコピー  

（さらに長くしたい場合は Meta の「長期トークン」ドキュメントを参照。GitHub Secrets に保存すれば、普段は触りません。）

### D-2.5. 自動延長の設定（推奨・60日切れ対策）

`config/instagram.env` に Meta アプリの ID / シークレットを追加すると、同期のたびにトークン延長を自動確認できます。

1. Meta → **マイアプリ** → 対象アプリ → **設定** → **ベーシック**  
2. **アプリ ID** と **app secret**（表示）をコピー  
3. `config/instagram.env` に追記:

```
INSTAGRAM_APP_ID=数字のみ
INSTAGRAM_APP_SECRET=英数字
```

4. 初回延長:

```bash
bash scripts/extend_instagram_token.sh
```

5. GitHub を使う場合、Secrets にも同じく `INSTAGRAM_APP_ID` / `INSTAGRAM_APP_SECRET` を登録  

`bash scripts/run_sync.sh` 実行時、有効期限が **14日以内** なら自動で延長します。GitHub Actions の日次同期でも同様です。  
延長後は表示された新トークンを **GitHub Secret `INSTAGRAM_ACCESS_TOKEN` にも反映**してください（Actions 内だけの更新では次回以降の Secret は古いままです）。

手動で強制延長: `bash scripts/extend_instagram_token.sh --force`

### D-3. ページのアクセストークン（推奨）

1. 再び **Graph API エクスプローラ**  
2. **ユーザーまたはページ** で、連携した **Facebook ページ** を選ぶ  
3. トークン欄に **ページのアクセストークン** が出る → それをコピー（これを最終的に使う）

---

## E. このフォルダを GitHub に置く

1. <https://github.com/new> で新しいリポジトリ（例: `saya-portfolio`）を **空で** 作成  
2. パソコンでこの `portfolio_site` フォルダを開く  
3. **ターミナル**（Mac: ターミナル.app）で次を実行（`YOUR_USER` と `REPO` は自分の名前に置き換え）:

```bash
cd このフォルダのパス/portfolio_site
git init
git add .
git commit -m "Initial portfolio site"
git branch -M main
git remote add origin https://github.com/YOUR_USER/REPO.git
git push -u origin main
```

※ GitHub Desktop を使っている場合は「リポジトリを作成 → このフォルダを追加 → Publish」でも同じです。

---

## F. GitHub Secrets（トークン登録・3分）

1. GitHub のリポジトリページ → **Settings** → **Secrets and variables** → **Actions**  
2. **New repository secret** を2回押して、次を登録:

| Name | Value |
|------|--------|
| `INSTAGRAM_ACCESS_TOKEN` | D-3 でコピーしたトークン |
| `INSTAGRAM_USER_ID` | 下の「ID の調べ方」 |
| `INSTAGRAM_APP_ID` | D-2.5（自動延長・任意だが推奨） |
| `INSTAGRAM_APP_SECRET` | D-2.5（自動延長・任意だが推奨） |

### Instagram ユーザー ID の調べ方（1回）

パソコンで:

```bash
cd このフォルダ/portfolio_site
bash scripts/setup_instagram_env.sh
```

`config/instagram.env` を開き、`INSTAGRAM_ACCESS_TOKEN=` の右にトークンを貼って保存。

続けて:

```bash
bash scripts/run_sync.sh
# 初回だけ pip が入る場合あり

python3 scripts/get_instagram_user_id.py
```

表示された `INSTAGRAM_USER_ID=...` の **数字部分** を、GitHub Secret `INSTAGRAM_USER_ID` に登録。

確認:

```bash
python3 scripts/verify_instagram_config.py
```

`OK` と出れば成功です。

---

## G. 初回同期のテスト

### 方法1: GitHub 上で（おすすめ・ターミナル不要）

1. GitHub リポジトリ → **Actions** タブ  
2. 左の **Sync Instagram Diary** → **Run workflow** → **Run workflow**  
3. 緑のチェックになったら **data/diary.json** と **images/diary/** が更新されているか確認  
4. サイトを開き **Diary** ページを表示

### 方法2: パソコンで

```bash
bash scripts/run_sync.sh
git add data/diary.json images/diary/
git commit -m "Update diary from Instagram"
git push
```

---

## Netlify とつなぐ（サイトを自動更新）

Drop だけだと Git の更新がサイトに反映されません。**GitHub 連携**を推奨します。

1. <https://app.netlify.com/> → 対象サイト → **Site configuration** → **Build & deploy**  
2. **Link repository** → さきほどの GitHub リポジトリを選択  
3. Build command: **空**、Publish directory: **/**（リポジトリ直下が `index.html` の場合）  
4. 保存後、Actions で同期 → push されるたびに Netlify が再公開されます  

---

## あとから Instagram に投稿したら？

**何もしなくて大丈夫です。**  
毎日 **12:00・24:00（日本時間）** に GitHub Actions がクラウド上で自動実行され、Diary が更新されます（パソコン電源は不要）。

急ぎで反映したいときだけ:

- GitHub → **Actions** → **Sync Instagram Diary** → **Run workflow**

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| Actions が赤い | Actions のログを開く。トークン期限切れなら `bash scripts/extend_instagram_token.sh --force` または D-2〜D-3 をやり直し Secrets を更新 |
| Diary が空 | Instagram に画像付き投稿があるか確認。動画のみの投稿はスキップされます |
| `instagram_business_account` が無い | B の Facebook ページ連携をやり直す |
| 403 / 権限エラー | C のテスター追加・権限チェックを見直す |

---

## ファイルの場所（参考）

| ファイル | 意味 |
|----------|------|
| `data/diary.json` | サイトが読む日記データ（自動更新） |
| `images/diary/*.jpg` | 投稿画像（自動ダウンロード） |
| `config/instagram.env` | パソコンでのテスト用（Git に入れない） |
| `.github/workflows/sync-instagram-diary.yml` | 毎日12:00・24:00 JST の自動同期（GitHub クラウド） |

---

## サポート用メモ（渡す人向け）

- サイトの文言・リンク・メールは `js/site-config.js`  
- Diary の見た目は `diary.html` / `css/styles.css`  
- 同期ロジックは `scripts/sync_instagram_diary.py`
