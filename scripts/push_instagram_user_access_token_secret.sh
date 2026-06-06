#!/usr/bin/env bash
# INSTAGRAM_USER_ACCESS_TOKEN だけ GitHub Secrets に登録する
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/config/instagram.env"
REPO="${GITHUB_REPO:-trokzkgnbr/sayaka-site}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "× $ENV_FILE がありません" >&2
  exit 1
fi

if [[ -z "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]]; then
  echo "× GH_TOKEN を export してから実行してください。" >&2
  echo "  https://github.com/settings/tokens （repo の Secrets 書き込み権限）" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

if [[ -z "${INSTAGRAM_USER_ACCESS_TOKEN:-}" ]]; then
  python3 "$ROOT/scripts/ensure_instagram_user_access_token.py"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if ! python3 -c "import nacl" 2>/dev/null; then
  python3 -m pip install --user PyNaCl
fi

python3 "$ROOT/scripts/push_github_secret.py" \
  --name INSTAGRAM_USER_ACCESS_TOKEN \
  --value "$INSTAGRAM_USER_ACCESS_TOKEN" \
  --repo "$REPO"
