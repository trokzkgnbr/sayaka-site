#!/usr/bin/env bash
# Blog 管理サーバー（公開サイトには載せない）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/config/admin.env"
EXAMPLE="$ROOT/config/admin.env.example"

if [[ ! -f "$ENV_FILE" && -f "$EXAMPLE" ]]; then
  cp "$EXAMPLE" "$ENV_FILE"
  chmod 600 "$ENV_FILE" 2>/dev/null || true
  echo "初回: config/admin.env を作成しました"
  echo "起動後、ブラウザでパスワードを設定できます"
fi

exec python3 "$ROOT/scripts/diary_admin_server.py"
