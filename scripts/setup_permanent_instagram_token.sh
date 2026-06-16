#!/usr/bin/env bash
# 半永久 Instagram トークンを一度設定する（D-2.6）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/config/instagram.env"

echo "=== Instagram 半永久トークン設定 ==="
echo ""
echo "前提: docs/INSTAGRAM_DIARY_SETUP.md の D-1（ユーザートークン）と D-2（延長）まで完了していること"
echo ""

if [[ ! -f "$ENV_FILE" ]]; then
  bash "$ROOT/scripts/setup_instagram_env.sh"
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

for key in INSTAGRAM_APP_ID INSTAGRAM_APP_SECRET INSTAGRAM_USER_ID; do
  if [[ -z "${!key:-}" ]]; then
    echo "× instagram.env の $key が空です" >&2
    exit 1
  fi
done

if [[ -z "${INSTAGRAM_USER_ACCESS_TOKEN:-}" ]]; then
  if [[ -z "${INSTAGRAM_ACCESS_TOKEN:-}" ]]; then
    echo "× INSTAGRAM_ACCESS_TOKEN または INSTAGRAM_USER_ACCESS_TOKEN が必要です" >&2
    exit 1
  fi
  echo "INSTAGRAM_USER_ACCESS_TOKEN を取得しています…"
  python3 "$ROOT/scripts/ensure_instagram_user_access_token.py"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

python3 "$ROOT/scripts/maintain_instagram_tokens.py" --force --write-env

echo ""
echo "=== 確認 ==="
python3 "$ROOT/scripts/check_instagram_token.py"

echo ""
echo "GitHub Actions を使う場合:"
echo "  1. export GH_TOKEN='ghp_...'  （repo Secrets 書き込み権限）"
echo "  2. bash scripts/setup_github_secrets.sh"
echo ""
echo "自動 Secrets 更新（任意）:"
echo "  GitHub Secret に INSTAGRAM_SECRETS_PAT を追加すると、同期のたびにトークンが自動更新されます。"
echo "  （Fine-grained PAT: sayaka-site → Secrets 書き込み）"
