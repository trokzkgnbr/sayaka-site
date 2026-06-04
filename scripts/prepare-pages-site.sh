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

shopt -s nullglob
for html in "$ROOT"/*.html; do
  cp "$html" "$OUT/"
done

for dir in css js images data; do
  if [[ -d "$ROOT/$dir" ]]; then
    cp -R "$ROOT/$dir" "$OUT/"
  fi
done

echo "Prepared $(find "$OUT" -type f | wc -l | tr -d ' ') files in $OUT"
