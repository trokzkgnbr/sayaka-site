# Blog 定期同期 — 24:05 JST テスト手順

## 2026-06-04 お昼（12:00 JST）に動かなかった調査結果

| 確認項目 | 結果 |
|----------|------|
| 12:00 JST（03:00 UTC）の `schedule` 実行 | **なし**（Actions 履歴に 0 件） |
| 同日の `push` による同期 | あり（01:40〜02:06 JST のデプロイ時） |
| `main` の workflow に schedule | **あり**（01:45 JST 時点で復帰済み） |
| リポジトリ | public・Actions 有効・workflow `active` |
| `data/diary.json` の更新 | 12:00 前後の `chore(blog)` コミット **なし** |

### 想定される原因（優先度順）

1. **毎時 0 分の cron 集中**  
   GitHub 公式: 負荷の高い時間帯（毎時 **:00**）は scheduled workflow が **遅延・ドロップ** されうる。  
   旧設定 `0 3 * * *` / `0 15 * * *` はちょうど 12:00 / 24:00 JST の **0 分** に相当。

2. **schedule 実行が一度も成功していない**  
   リポジトリ作成以来、`event: schedule` の実行が **1 回も記録されていない**。初回は最大で数時間ずれることもあるが、お昼の実行も来なかった。

3. **リポジトリ側で schedule が無効**（要確認）  
   GitHub → **Settings → Actions** に  
   「Scheduled workflows have been disabled」等のバナーがないか確認。

4. **除外されなかったもの**  
   - トークン・Secrets（手動・push では成功している）  
   - workflow の YAML 構文（push トリガーは成功）  
   - プライベートリポ制限（public）

### 対策（実施済み）

cron を **毎時 5 分（UTC）** に変更:

- `5 3 * * *` → **12:05 JST**
- `5 15 * * *` → **24:05 JST**

---

## 今夜 24:05 JST のテスト手順

1. **Actions** を開く:  
   https://github.com/trokzkgnbr/sayaka-site/actions/workflows/sync-instagram-diary.yml

2. **00:05〜00:20 JST** のあいだに新しい行が増えるか見る（最大 15 分遅れることあり）。

3. 成功の目安:
   - イベント列が **`schedule`**（`push` ではない）
   - 緑のチェック
   - ログに `Blog 投稿数: N`
   - 必要なら `chore(blog): sync from Instagram` のコミット

4. 00:20 過ぎても `schedule` が無い場合:
   - Settings → Actions で schedule 無効バナーを確認
   - **Run workflow** で手動同期（同期自体は動くか切り分け）
   - 翌日 12:05 JST を再確認

5. サイト反映: GitHub にコミットが付いてから **Deploy GitHub Pages** が 1〜5 分で更新。
