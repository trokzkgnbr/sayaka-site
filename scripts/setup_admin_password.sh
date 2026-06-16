#!/usr/bin/env bash
# 管理用パスワードを設定（平文は config/admin.env に保存しない）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="$ROOT/config/admin.env.example"
TARGET="$ROOT/config/admin.env"

if [[ ! -f "$EXAMPLE" ]]; then
  echo "× $EXAMPLE がありません" >&2
  exit 1
fi

if [[ -f "$TARGET" ]]; then
  echo "すでに存在します: config/admin.env"
  read -r -p "上書きしますか？ [y/N] " ans
  [[ "${ans,,}" == "y" ]] || exit 0
fi

read -r -s -p "Blog 管理用パスワード（入力は画面に表示されません）: " pass1
echo
read -r -s -p "もう一度: " pass2
echo

if [[ -z "$pass1" ]]; then
  echo "× 空のパスワードは使えません" >&2
  exit 1
fi
if [[ "$pass1" != "$pass2" ]]; then
  echo "× 一致しません" >&2
  exit 1
fi

python3 "$ROOT/scripts/setup_admin_password.py" --password-stdin <<<"$pass1"

echo "OK: config/admin.env を作成しました"
echo "起動: bash scripts/run_diary_admin.sh"
