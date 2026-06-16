#!/usr/bin/env bash
# Blog 管理サーバー（公開サイトには載せない）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/config/admin.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "× config/admin.env がありません" >&2
  echo "  bash scripts/setup_admin_password.sh" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

exec python3 "$ROOT/scripts/diary_admin_server.py"
