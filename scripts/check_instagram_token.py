#!/usr/bin/env python3
"""Instagram トークンが Blog 同期に使えるか確認（ローカル / 手順案内用）。"""

from __future__ import annotations

import sys

from ci_resolve_instagram_token import probe_token, try_refresh
from lib_instagram import InstagramConfigError, load_config, load_meta_app_credentials

import os


def main() -> int:
    try:
        cfg = load_config()
    except InstagramConfigError as exc:
        print(f"× {exc}")
        return 1

    token = cfg["token"]
    user_id = cfg["user_id"]
    err = probe_token(token, user_id)
    if err is None:
        print("OK: このトークンで Instagram 投稿を取得できます。")
        print(f"   INSTAGRAM_USER_ID={user_id}")
        return 0

    print(f"× 現在のトークンでは取得できません:\n  {err}")
    app_id = os.environ.get("INSTAGRAM_APP_ID", "").strip()
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    if app_id and app_secret:
        try:
            app_id, app_secret = load_meta_app_credentials()
            new_token, label = try_refresh(token, app_id, app_secret, user_id)
            if new_token:
                print(f"OK: 再取得したページトークンは有効です（{label}）。")
                print("   次: 表示されたトークンを GitHub Secrets の INSTAGRAM_ACCESS_TOKEN に保存")
                print(f"\nINSTAGRAM_ACCESS_TOKEN={new_token}")
                return 0
        except InstagramConfigError:
            pass

    print("\n対処: docs/INSTAGRAM_DIARY_SETUP.md の D-1〜D-3 をやり直し、")
    print("      ページのアクセストークンを Secrets に登録してください。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
