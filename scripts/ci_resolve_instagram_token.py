#!/usr/bin/env python3
"""
GitHub Actions 用: Blog 同期に使える Instagram トークンを決める。

1. Secrets のトークンでメディア取得を試す
2. 失敗かつ APP_ID/SECRET があるときだけページトークンを再取得
3. 成功したトークンを GITHUB_OUTPUT に書く
"""

from __future__ import annotations

import os
import sys

from lib_instagram import (
    InstagramAPIError,
    InstagramConfigError,
    iter_media,
    load_config,
    load_meta_app_credentials,
    refresh_instagram_access_token,
)


def write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def probe_token(token: str, user_id: str) -> str | None:
    """成功なら None、失敗ならエラーメッセージ。"""
    try:
        iter_media(token, user_id, 1)
        return None
    except InstagramAPIError as exc:
        return str(exc)


def main() -> int:
    try:
        cfg = load_config()
    except InstagramConfigError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    token = cfg["token"]
    user_id = cfg["user_id"]
    err = probe_token(token, user_id)
    if err is None:
        print("既存トークンで Instagram API に接続できました。")
        write_github_output("value", token)
        return 0

    print(f"既存トークンで接続できません: {err}", file=sys.stderr)

    app_id = os.environ.get("INSTAGRAM_APP_ID", "").strip()
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        print(
            "::error::INSTAGRAM_ACCESS_TOKEN を更新してください。"
            "（Meta エクスプローラでページトークンを取得 → GitHub Secrets）",
            file=sys.stderr,
        )
        return 1

    try:
        app_id, app_secret = load_meta_app_credentials()
        new_token, label = refresh_instagram_access_token(
            token, app_id, app_secret, user_id
        )
    except InstagramConfigError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1
    except InstagramAPIError as exc:
        print(f"::error::トークン再取得に失敗: {exc}", file=sys.stderr)
        print(
            "Meta 開発者アプリで pages_show_list 等の権限を付与し、"
            "長期ページトークンを Secrets の INSTAGRAM_ACCESS_TOKEN に設定してください。",
            file=sys.stderr,
        )
        return 1

    err2 = probe_token(new_token, user_id)
    if err2 is not None:
        print(f"::error::再取得トークンでも接続できません: {err2}", file=sys.stderr)
        return 1

    print(f"ページトークンを再取得しました（{label}）。")
    print(
        "この実行では新トークンを使用します。"
        "次回以降も成功させるには Secrets の INSTAGRAM_ACCESS_TOKEN を同じ値に更新してください。",
        file=sys.stderr,
    )
    write_github_output("value", new_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
