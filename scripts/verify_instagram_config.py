#!/usr/bin/env python3
"""Instagram 連携設定が正しいか確認する。"""

from __future__ import annotations

import sys

from lib_instagram import (
    InstagramAPIError,
    InstagramConfigError,
    load_config,
    verify_connection,
)


def main() -> int:
    try:
        cfg = load_config()
        info = verify_connection(cfg["token"], cfg["user_id"])
    except InstagramConfigError as exc:
        print(f"× {exc}")
        return 1
    except InstagramAPIError as exc:
        print(f"× API: {exc}")
        return 1

    print("OK Instagram 連携は問題なさそうです。")
    print(f"   アカウント: @{info['username']}")
    print(f"   ID: {info['user_id']}")
    print("\n次: bash scripts/run_sync.sh --dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
