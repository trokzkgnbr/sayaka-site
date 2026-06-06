#!/usr/bin/env python3
"""長期ユーザートークンを取得し config/instagram.env に保存する。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from lib_instagram import (
    InstagramAPIError,
    debug_token_info,
    exchange_long_lived_user_token,
    load_env_file,
    load_meta_app_credentials,
    site_root,
    update_env_file_value,
)

KEY = "INSTAGRAM_USER_ACCESS_TOKEN"


def derive_user_access_token(access_token: str, app_id: str, app_secret: str) -> str:
    info = debug_token_info(access_token, app_id, app_secret)
    if not info.get("is_valid", True):
        raise InstagramAPIError(
            "INSTAGRAM_ACCESS_TOKEN が無効です。Graph API エクスプローラで取り直してください。"
        )
    user_token, _ = exchange_long_lived_user_token(access_token, app_id, app_secret)
    return user_token


def main() -> int:
    root = site_root()
    env_path = root / "config" / "instagram.env"
    load_env_file(env_path)

    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not access_token:
        print("× INSTAGRAM_ACCESS_TOKEN が未設定です。", file=sys.stderr)
        return 1

    try:
        app_id, app_secret = load_meta_app_credentials()
        user_token = derive_user_access_token(access_token, app_id, app_secret)
    except InstagramAPIError as exc:
        print(f"× {exc}", file=sys.stderr)
        print(
            "\nヒント: Graph API エクスプローラでユーザートークンを取得し、"
            "INSTAGRAM_USER_ACCESS_TOKEN として登録してください。",
            file=sys.stderr,
        )
        return 1

    if env_path.is_file():
        update_env_file_value(env_path, KEY, user_token)
        print(f"OK: {env_path} に {KEY} を保存しました。")
    else:
        print(f"OK: {KEY} を取得しました（instagram.env なしのためファイル未更新）。")

    if os.environ.get("EXPORT_INSTAGRAM_USER_ACCESS_TOKEN") == "1":
        print(f"{KEY}={user_token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
