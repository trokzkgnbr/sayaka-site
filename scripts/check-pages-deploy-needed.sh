#!/usr/bin/env bash
# main から組み立てた _site と gh-pages の差分を見る（0=デプロイ要, 1=不要）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="${1:-$ROOT/_site}"
LIVE_DIR="${2:-$ROOT/_gh-pages-live}"

if [[ ! -d "$SITE_DIR" ]]; then
  echo "× site dir not found: $SITE_DIR" >&2
  exit 2
fi

if [[ ! -d "$LIVE_DIR" ]] || [[ -z "$(find "$LIVE_DIR" -type f 2>/dev/null | head -1)" ]]; then
  echo "初回デプロイ（gh-pages が空）"
  exit 0
fi

if diff -qr "$SITE_DIR" "$LIVE_DIR" >/dev/null 2>&1; then
  echo "変更なし — デプロイをスキップ"
  exit 1
fi

echo "変更あり — デプロイします"
exit 0
