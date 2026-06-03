#!/usr/bin/env bash
# 初回: instagram.env のひな形を作る
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="$ROOT/config/instagram.env.example"
TARGET="$ROOT/config/instagram.env"

if [[ -f "$TARGET" ]]; then
  echo "すでに存在します: config/instagram.env"
  exit 0
fi

cp "$EXAMPLE" "$TARGET"
chmod 600 "$TARGET" 2>/dev/null || true
echo "作成しました: config/instagram.env"
echo "メモ帳などで INSTAGRAM_ACCESS_TOKEN を貼り付けて保存してください。"
echo "手順: docs/INSTAGRAM_DIARY_SETUP.md"
