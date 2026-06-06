#!/usr/bin/env python3
"""GitHub Actions: INSTAGRAM_USER_ACCESS_TOKEN を Secret または ACCESS_TOKEN から解決する。"""

from __future__ import annotations

import os
import sys

from ensure_instagram_user_access_token import derive_user_access_token
from lib_instagram import InstagramAPIError, load_meta_app_credentials


def write_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not path:
        return
    delimiter = "USER_TOKEN_EOF"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def main() -> int:
    explicit = os.environ.get("INSTAGRAM_USER_ACCESS_TOKEN", "").strip().strip('"').strip("'")
    if explicit:
        print("INSTAGRAM_USER_ACCESS_TOKEN（Secret）を使用します。")
        write_output("value", explicit)
        return 0

    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not access_token:
        print("::warning::INSTAGRAM_USER_ACCESS_TOKEN 未設定かつ ACCESS_TOKEN も空です。", file=sys.stderr)
        write_output("value", "")
        return 0

    try:
        app_id, app_secret = load_meta_app_credentials()
        user_token = derive_user_access_token(access_token, app_id, app_secret)
    except InstagramAPIError as exc:
        print(f"::warning::ユーザートークン自動取得に失敗: {exc}", file=sys.stderr)
        write_output("value", "")
        return 0

    print("ACCESS_TOKEN から長期ユーザートークンを導出しました（Secret 未設定時のフォールバック）。")
    write_output("value", user_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
