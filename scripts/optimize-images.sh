#!/usr/bin/env bash
# Gallery / Home 画像を Web 向けに最適化（PNG→JPEG、長辺リサイズ）
set -euo pipefail

MAX_DIM=2400
QUALITY=85
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

optimize_file() {
  local f="$1"
  local tmp="${f}.opt.tmp.jpg"
  sips -Z "$MAX_DIM" -s format jpeg -s formatOptions "$QUALITY" "$f" --out "$tmp" >/dev/null
  mv "$tmp" "$f"
  echo "  ok: $f ($(wc -c <"$f" | tr -d ' ') bytes)"
}

echo "Optimizing gallery + home images (max ${MAX_DIM}px, quality ${QUALITY})..."
while IFS= read -r -d '' f; do
  optimize_file "$f"
done < <(find "$ROOT/images/gallery" "$ROOT/images/home" -type f \( -name '*.jpg' -o -name '*.jpeg' \) ! -name '*.opt.tmp.jpg' -print0)

echo "Done."
