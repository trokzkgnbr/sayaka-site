# Diary × Instagram 連携セットアップ（非エンジニア向け）

更新日: 2026-06-01 JST

このサイトの **Blog** は、Instagram **@4mnion** に投稿した内容を **GitHub Actions（クラウド）で1日2回自動**で取り込みます（**12:05・24:05 日本時間**・数分のずれあり）。  
（画像1枚・正方形の投稿を想定。動画・リールは取り込みません。）

※ サイト右上の Instagram / X リンク（**@pikinsaya**）とは別アカウントです。

**お金はかかりません**（GitHub Pages + GitHub Actions + Meta API は無料枠で足ります）。

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

初回が終われば **あとは自動** です（毎日 **12:05・24:05 JST** 頃に GitHub 上で同期 → Pages に反映）。

---

## 必要なもの

| もの | 用途 |
|------|------|
| Instagram **@4mnion**（Diary 用・1つ） | 日記の元データ |
| Facebook アカウント | Meta 開発者用 |
| GitHub アカウント（無料） | 自動同期の実行場所 |
| （任意）独自ドメイン | GitHub Pages に向ける DNS |

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

`bash scripts/run_sync.sh` 実行時、有効期限が **14日以内** なら自動で延長します。  
GitHub Actions（`Sync Instagram Diary`）でも、同期の直前に同じ延長を試します（`INSTAGRAM_APP_ID` / `INSTAGRAM_APP_SECRET` が必要）。

延長後は表示された新トークンを **GitHub Secret `INSTAGRAM_ACCESS_TOKEN` にも反映**してください（Actions 内だけの更新では次回以降の Secret は古いままです）。  
**すでに切れたトークン**は延長できません。その場合は D-1〜D-3 で取り直し、`INSTAGRAM_USER_ACCESS_TOKEN`（延長済みユーザー トークン）を Secret に入れておくと、次回から自動再取得を試せます。

手動で強制延長: `bash scripts/extend_instagram_token.sh --force`

### D-2.6. 半永久トークン（推奨・30日切れ対策）

Meta の仕様:

| トークン | 期限 |
|----------|------|
| 短期ユーザートークン | 数時間 |
| 長期ユーザートークン | **約60日**（デバッガーで30〜60日と表示されることも） |
| **ページトークン**（長期ユーザートークンから取得） | **無期限**（Debugger で Expires: **Never**） |

30日と表示されているのは、**ページトークンを直接コピーした**か、**ユーザートークン**の期限です。  
Blog 同期では **長期ユーザートークン → ページトークン再取得** の順が正解で、ページ側は実質ずっと使えます。

**一度だけ実行（ローカル）:**

```bash
bash scripts/setup_permanent_instagram_token.sh
```

これで `INSTAGRAM_USER_ACCESS_TOKEN`（約60日・同期のたびに自動延長）と  
無期限の `INSTAGRAM_ACCESS_TOKEN`（ページ）が `instagram.env` に保存されます。

**GitHub Actions 向け（任意・完全自動）:**

1. 上記のあと `bash scripts/setup_github_secrets.sh` で Secrets 登録  
2. （任意）Fine-grained PAT（`sayaka-site` の Secrets 書き込み）を Secret **`INSTAGRAM_SECRETS_PAT`** に登録  
   → 同期のたびに延長したトークンが Secrets に自動反映され、手動更新不要

同期ワークフローは **毎回** ユーザートークンからページトークンを取り直し、  
ユーザートークンは **残り30日以内** なら自動延長します。

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
| `INSTAGRAM_ACCESS_TOKEN` | D-3 でコピーした **ページ** トークン（必須） |
| `INSTAGRAM_USER_ID` | 下の「ID の調べ方」 |
| `INSTAGRAM_APP_ID` | D-2.5（自動延長・推奨） |
| `INSTAGRAM_APP_SECRET` | D-2.5（自動延長・推奨） |
| `INSTAGRAM_USER_ACCESS_TOKEN` | （推奨）D-1 の **ユーザー** トークン（延長済み）。半永久運用の要 |
| `INSTAGRAM_SECRETS_PAT` | （任意）GitHub PAT。設定すると同期時に Secrets を自動更新 |

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

## サイトを自動更新（GitHub Pages）

本番は **GitHub Pages**（ワークフロー `Deploy GitHub Pages`）を使います。詳細は [`GITHUB_PAGES_SETUP.md`](GITHUB_PAGES_SETUP.md)。

- Blog 同期で `main` が更新される → 自動で再デプロイ
- 初回 URL: https://trokzkgnbr.github.io/sayaka-site/

---

## あとから Instagram に投稿したら？

**何もしなくて大丈夫です。**  
毎日 **12:05・24:05（日本時間）頃** に GitHub Actions がクラウド上で自動実行され、Blog が更新されます（パソコン電源は不要）。

### 定期実行が動かないとき（調査メモ）

**2026-06-06 時点の調査結果**

| 現象 | 原因 |
|------|------|
| 12:05 JST に来ない | GitHub `schedule` が **数時間遅れる・欠落** する（公式: 毎時 :00 付近は特に混雑） |
| 来ても赤い | 過去ログでは **Instagram トークン失敗**（`Resolve Instagram token for sync`）が主因 |
| 手動は成功する | Secrets は有効。schedule 単体の遅延・失敗と切り分け可能 |

**実施済み対策（workflow）**

- お昼 **12:05 / 12:17 / 12:35 / 13:05 JST**、深夜 **24:05 / 24:17 / 24:35 / 翌1:05 JST** の **8 スロット**（遅延・欠落の冗長化）
- 直近 **90 分以内** に同期済みなら schedule 実行をスキップ（重複 API 呼び出し防止）
- 同期前にトークン延長 → 失敗時は `INSTAGRAM_USER_ACCESS_TOKEN` でページトークン再取得

**確認手順**

1. **Actions** でイベント **`schedule`** の実行があるか（`push` だけなら定期はまだ来ていない）
2. **Settings → Actions** に「Scheduled workflows are disabled」がないか（60 日無操作で止まる場合あり）
3. 失敗時はログの **Resolve Instagram token for sync** を確認 → D-1〜D-3 でトークン更新、`INSTAGRAM_USER_ACCESS_TOKEN` も登録
4. 急ぎは **Run workflow** で手動同期

**同期のルール（重要）**

- Instagram から取得した **直近 50 件** だけ、追加・更新・削除を反映します（Instagram で消した投稿は次の同期でサイトからも消えます）。
- アカウントの投稿数が **50 件未満** のときは全投稿を取得するため、Instagram で消した投稿は **日付に関係なく** Blog から削除されます。
- **51 件目より古い** 投稿は、取得上限に達しているときだけ **サイトに残ります**（勝手には消しません）。
- 同期後は **整合性チェック** を実行し、消えるべき投稿が残っていたら Actions を失敗させます（`managedInstagramIds` と照合）。
- **並び順**は Instagram のプロフィールと同じ（新しい順）。同日の投稿も `publishedAt`（投稿時刻）と API 返却順で揃えます（日付だけの並べ替えはしません）。
- 動画・リールは Blog に載せませんが、Instagram 上にある場合は **削除扱いにしません**（既存の Blog 投稿があれば維持）。
- Instagram から消えた投稿は Blog からも削除します（**Instagram と常に一致**）。トークン切れなどで API に接続できないときだけ Blog を維持します。
- 一覧ページは **30 件ずつ** 表示し、31 件以上あるときは下部の **next →** で次のページへ進みます。

**同期と公開**

- **Blog の投稿本文・画像** … `Sync Instagram Diary` が `data/diary.json` と `images/diary/` を更新
- **本番サイト** … Instagram 同期で **データに変更があったときだけ**、同じワークフロー内で `gh-pages` へ公開（変更なしの日はデプロイしない）
- HTML/CSS などサイト全体の更新は、従来どおり `Deploy GitHub Pages`（`main` への push 時）
- Instagram 同期は **毎日 12:05・24:05 JST 頃** と **手動（Run workflow）** のみ（通常のサイト更新 push では走りません）
- Blog が古いままなら、Actions の成否と https://trokzkgnbr.github.io/sayaka-site/data/diary.json を確認

急ぎで反映したいときだけ:

- GitHub → **Actions** → **Sync Instagram Diary** → **Run workflow**

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| Actions が赤い（190 / pages_show_list） | **ページトークン**の期限切れまたは権限不足。D-1〜D-3 をやり直し `INSTAGRAM_ACCESS_TOKEN` を更新（`bash scripts/setup_github_secrets.sh` でも可）。ローカル確認: `python3 scripts/check_instagram_token.py` |
| トークンが30日で切れる | D-2.6 `bash scripts/setup_permanent_instagram_token.sh` で **ユーザートークン + 無期限ページトークン** に切り替え |
| Actions が赤い（投稿 0 件） | 同上。**Blog が空になっていたら** `git checkout 3a68d46 -- data/diary.json images/diary/` で復元してからトークン更新 → 手動 Run workflow |
| Actions が赤い（その他） | ログの **Resolve Instagram token for sync** を確認 |
| Blog が空・古い | Actions → **Sync Instagram Diary** を手動実行。`data/diary.json` のコミットがあるか確認 |
| 見た目だけ新しい | 投稿データは Actions 同期。`git push` だけでは増えません |
| 動画だけの投稿が出ない | 動画・リールはスキップされます（画像付き投稿を確認） |
| `instagram_business_account` が無い | B の Facebook ページ連携をやり直す |
| 403 / 権限エラー | C のテスター追加・権限チェックを見直す |

---

## ファイルの場所（参考）

| ファイル | 意味 |
|----------|------|
| `data/diary.json` | サイトが読む日記データ（自動更新） |
| `images/diary/*.jpg` | 投稿画像（自動ダウンロード） |
| `config/instagram.env` | パソコンでのテスト用（Git に入れない） |
| `.github/workflows/sync-instagram-diary.yml` | 毎日12:05・24:05 JST 頃の自動同期 + 手動実行（GitHub クラウド） |

---

## サポート用メモ（渡す人向け）

- サイトの文言・リンク・メールは `js/site-config.js`  
- Diary の見た目は `diary.html` / `css/styles.css`  
- 同期ロジックは `scripts/sync_instagram_diary.py`
