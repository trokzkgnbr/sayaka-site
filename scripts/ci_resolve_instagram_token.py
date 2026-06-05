#!/usr/bin/env python3
"""
GitHub Actions 用: Blog 同期に使える Instagram トークンを決める。

1. INSTAGRAM_ACCESS_TOKEN（ページトークン想定）でメディア取得を試す
2. 失敗時、INSTAGRAM_USER_ACCESS_TOKEN があればそれでページトークンを再取得
3. なければ ACCESS_TOKEN をユーザートークンとして再取得を試す
4. 成功したトークンを GITHUB_OUTPUT に書く
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

TOKEN_HELP = (
    "Graph API エクスプローラでユーザートークンを取得 "
    "（pages_show_list, pages_read_engagement, instagram_basic）→ "
    "Facebook ページを選びページトークンをコピー → "
    "GitHub Secrets の INSTAGRAM_ACCESS_TOKEN を更新。"
    " 手順: docs/INSTAGRAM_DIARY_SETUP.md の D-1〜D-3"
)


def write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not path:
        return
    delimiter = "INSTAGRAM_TOKEN_EOF"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def probe_token(token: str, user_id: str) -> str | None:
    """成功なら None、失敗ならエラーメッセージ。"""
    if not token:
        return "トークンが空です"
    try:
        iter_media(token, user_id, 1)
        return None
    except InstagramAPIError as exc:
        return str(exc)


def try_refresh(
    user_token: str,
    app_id: str,
    app_secret: str,
    instagram_user_id: str,
) -> tuple[str | None, str | None]:
    try:
        page_token, label = refresh_instagram_access_token(
            user_token,
            app_id,
            app_secret,
            instagram_user_id,
            user_token=user_token,
        )
    except (InstagramConfigError, InstagramAPIError) as exc:
        return None, str(exc)
    err = probe_token(page_token, instagram_user_id)
    if err is not None:
        return None, f"再取得トークンでも接続不可: {err}"
    return page_token, label


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

    print(f"::warning::既存トークンで接続できません: {err}", file=sys.stderr)

    app_id = os.environ.get("INSTAGRAM_APP_ID", "").strip()
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        print(f"::error::{TOKEN_HELP}", file=sys.stderr)
        return 1

    try:
        app_id, app_secret = load_meta_app_credentials()
    except InstagramConfigError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    refresh_candidates: list[tuple[str, str]] = []
    user_access = os.environ.get("INSTAGRAM_USER_ACCESS_TOKEN", "").strip().strip('"').strip("'")
    if user_access:
        refresh_candidates.append(("INSTAGRAM_USER_ACCESS_TOKEN", user_access))
    if token and token != user_access:
        refresh_candidates.append(("INSTAGRAM_ACCESS_TOKEN（ユーザートークンとして再試行）", token))

    last_err = err
    for label, candidate in refresh_candidates:
        print(f"ページトークン再取得を試行: {label}", file=sys.stderr)
        page_token, refresh_info = try_refresh(candidate, app_id, app_secret, user_id)
        if page_token:
            print(f"ページトークンを再取得しました（{refresh_info}）。")
            print(
                "::warning::Secrets の INSTAGRAM_ACCESS_TOKEN をログに表示された新トークンに更新してください。",
                file=sys.stderr,
            )
            write_github_output("value", page_token)
            return 0
        last_err = refresh_info or last_err
        print(f"::warning::{label} で再取得失敗: {refresh_info}", file=sys.stderr)

    print(f"::error::トークン再取得に失敗しました: {last_err}", file=sys.stderr)
    print(f"::error::{TOKEN_HELP}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
