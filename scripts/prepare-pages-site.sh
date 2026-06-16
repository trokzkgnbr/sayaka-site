#!/usr/bin/env bash
# GitHub Pages 用: 公開ファイルだけを _site/ に集める（scripts/ や docs/ は含めない）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/_site}"

rm -rf "$OUT"
mkdir -p "$OUT"

if [[ -f "$ROOT/.nojekyll" ]]; then
  cp "$ROOT/.nojekyll" "$OUT/"
else
  : >"$OUT/.nojekyll"
fi

if [[ -f "$ROOT/CNAME" ]]; then
  cp "$ROOT/CNAME" "$OUT/"
fi

shopt -s nullglob
for html in "$ROOT"/*.html; do
  cp "$html" "$OUT/"
done

for dir in css js images data; do
  if [[ -d "$ROOT/$dir" ]]; then
    cp -R "$ROOT/$dir" "$OUT/"
  fi
done

ADMIN_PATH_FILE="$ROOT/config/blog-admin-path.txt"
if [[ -f "$ADMIN_PATH_FILE" && -d "$ROOT/admin" ]]; then
  ADMIN_PATH="$(tr -d '[:space:]' < "$ADMIN_PATH_FILE")"
  if [[ "$ADMIN_PATH" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    mkdir -p "$OUT/$ADMIN_PATH"
    cp -R "$ROOT/admin/." "$OUT/$ADMIN_PATH/"
    HASH=""
    if [[ -f "$ROOT/config/admin.env" ]]; then
      HASH="$(grep '^ADMIN_PASSWORD_HASH=' "$ROOT/config/admin.env" | cut -d= -f2- || true)"
    fi
    if [[ -z "$HASH" && -n "${ADMIN_PASSWORD_HASH:-}" ]]; then
      HASH="$ADMIN_PASSWORD_HASH"
    fi
    if [[ -n "$HASH" ]]; then
      python3 "$ROOT/scripts/generate_admin_auth_config.py" "$OUT/$ADMIN_PATH/auth-config.js" "$HASH"
      echo "Admin auth config: /${ADMIN_PATH}/auth-config.js"
    else
      echo "警告: ADMIN_PASSWORD_HASH 未設定 — サイト上の管理画面はパスワード保護されません" >&2
    fi
    mkdir -p "$OUT"
    {
      echo "User-agent: *"
      echo "Disallow: /${ADMIN_PATH}/"
    } >>"$OUT/robots.txt"
    echo "Admin UI (static): /${ADMIN_PATH}/"
  else
    echo "× config/blog-admin-path.txt の形式が不正です" >&2
    exit 1
  fi
fi

echo "Prepared $(find "$OUT" -type f | wc -l | tr -d ' ') files in $OUT"
