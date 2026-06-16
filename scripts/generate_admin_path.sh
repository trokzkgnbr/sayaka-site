#!/usr/bin/env bash
# 外出先公開用の秘密 URL パスを生成
set -euo pipefail
python3 - <<'PY'
import secrets

slug = "blog-mgt-" + secrets.token_hex(4)
print(slug)
print()
print("Render の環境変数 ADMIN_PATH に上の文字列を設定してください。")
print("管理画面 URL 例: https://<your-app>.onrender.com/" + slug + "/")
PY
