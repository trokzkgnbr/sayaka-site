#!/usr/bin/env bash
# アクセストークン延長（config/instagram.env を読み込む）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="$ROOT/config/instagram.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if ! python3 -c "import requests" 2>/dev/null; then
  python3 -m pip install --user -r "$ROOT/scripts/requirements-instagram-sync.txt"
fi

exec python3 "$ROOT/scripts/extend_instagram_token.py" "$@"
