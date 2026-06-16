#!/usr/bin/env python3
"""Instagram トークンが Blog 同期に使えるか確認（ローカル / 手順案内用）。"""

from __future__ import annotations

import os
import sys

from lib_instagram import (
    InstagramConfigError,
    debug_token_info,
    format_token_expiry,
    load_config,
    load_meta_app_credentials,
    probe_media_access,
    probe_token_connection,
)
from maintain_instagram_tokens import maintain_from_env, print_result


def main() -> int:
    try:
        cfg = load_config()
    except InstagramConfigError as exc:
        print(f"× {exc}")
        return 1

    token = cfg["token"]
    user_id = cfg["user_id"]
    conn_err, account = probe_token_connection(token, user_id)
    if conn_err is not None:
        print(f"× Instagram に接続できません:\n  {conn_err}")
    else:
        post_err = probe_media_access(token, user_id, require_posts=True)
        username = (account or {}).get("username") or user_id
        if post_err is None:
            print("OK: このトークンで Instagram 投稿を取得できます。")
        else:
            print(f"OK: @{username} に接続できます（API 上の投稿は 0 件）。")
            print("   Blog の既存データは維持されます。新規同期には @4mnion への画像投稿が必要です。")
        print(f"   INSTAGRAM_USER_ID={user_id}")
        try:
            app_id, app_secret = load_meta_app_credentials()
            page_info = debug_token_info(token, app_id, app_secret)
            print(
                f"   ページトークン: 種別={page_info.get('type', '?')}"
                f" / 期限={format_token_expiry(page_info)}"
            )
            user_access = os.environ.get("INSTAGRAM_USER_ACCESS_TOKEN", "").strip()
            if user_access:
                user_info = debug_token_info(user_access, app_id, app_secret)
                print(
                    f"   ユーザートークン: 種別={user_info.get('type', '?')}"
                    f" / 期限={format_token_expiry(user_info)}"
                )
        except InstagramConfigError:
            pass
        return 0

    print(f"× 現在の INSTAGRAM_ACCESS_TOKEN では取得できません:\n  {conn_err}")

    app_id = os.environ.get("INSTAGRAM_APP_ID", "").strip()
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    if app_id and app_secret:
        try:
            result = maintain_from_env(force_user_refresh=False, if_needed=False)
            err2 = probe_token_connection(result.page_token, user_id)[0]
            if err2 is None:
                print_result(result)
                print("OK: ページトークンを再取得すれば使えます。")
                print("   次: GitHub Secrets の INSTAGRAM_ACCESS_TOKEN を更新")
                print(f"\nINSTAGRAM_ACCESS_TOKEN={result.page_token}")
                return 0
            print(f"× 再取得後も取得できません:\n  {err2}")
        except Exception as exc:  # noqa: BLE001
            print(f"× 再取得に失敗: {exc}")

    print("\n対処: docs/INSTAGRAM_DIARY_SETUP.md の D-1〜D-3 をやり直し、")
    print("      ページトークンと INSTAGRAM_USER_ACCESS_TOKEN を Secrets に登録。")
    print("      @4mnion に画像付き投稿があるかも確認してください。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
