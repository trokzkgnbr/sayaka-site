#!/usr/bin/env python3
"""デプロイ用 auth-config.js を生成（平文パスワードは含めない）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: generate_admin_auth_config.py OUT/auth-config.js HASH", file=sys.stderr)
        return 1
    out = Path(sys.argv[1])
    pwd_hash = sys.argv[2].strip()
    if not pwd_hash.startswith("pbkdf2_sha256$"):
        print("× ADMIN_PASSWORD_HASH の形式が不正です", file=sys.stderr)
        return 1
    payload = {"hash": pwd_hash, "iterations": 600_000}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "window.ADMIN_AUTH=" + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
