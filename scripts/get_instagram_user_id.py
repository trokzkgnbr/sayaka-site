#!/usr/bin/env python3
"""アクセストークンから Instagram ユーザー ID を表示する（instagram.env 用）。"""

from __future__ import annotations

import sys
from pathlib import Path

from lib_instagram import InstagramAPIError, InstagramConfigError, discover_instagram_user_id, load_env_file, site_root


def main() -> int:
    root = site_root()
    load_env_file(root / "config" / "instagram.env")

    import os

    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not token:
        print(
            "INSTAGRAM_ACCESS_TOKEN を config/instagram.env に設定してから再実行してください。",
            file=sys.stderr,
        )
        return 1

    try:
        ig_id, label = discover_instagram_user_id(token)
    except InstagramAPIError as exc:
        print(f"× {exc}", file=sys.stderr)
        return 1

    print("次の1行を config/instagram.env に追加（または更新）してください:\n")
    print(f"INSTAGRAM_USER_ID={ig_id}")
    print(f"\n（検出: {label}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
