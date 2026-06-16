#!/usr/bin/env python3
"""
GitHub Actions 用: Blog 同期に使える Instagram ページトークンを決める。

半永久運用: INSTAGRAM_USER_ACCESS_TOKEN + APP_ID/SECRET からページトークンを再取得。
フォールバック: 既存 INSTAGRAM_ACCESS_TOKEN が使えるならそれを使う。
"""

from __future__ import annotations

import os
import sys

from lib_instagram import (
    InstagramAPIError,
    InstagramConfigError,
    load_config,
    probe_media_access,
)
from maintain_instagram_tokens import (
    export_github_outputs,
    maintain_from_env,
    print_result,
)

TOKEN_HELP = (
    "docs/INSTAGRAM_DIARY_SETUP.md の D-2.6（半永久トークン）を実行し、"
    " INSTAGRAM_USER_ACCESS_TOKEN / INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET を Secrets に登録。"
)


def write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not path:
        return
    delimiter = "INSTAGRAM_TOKEN_EOF"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def main() -> int:
    try:
        cfg = load_config()
    except InstagramConfigError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 1

    token = cfg["token"]
    user_id = cfg["user_id"]
    app_id = os.environ.get("INSTAGRAM_APP_ID", "").strip()
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    user_access = os.environ.get("INSTAGRAM_USER_ACCESS_TOKEN", "").strip()

    if app_id and app_secret and (user_access or token):
        try:
            result = maintain_from_env(if_needed=True)
            err = probe_media_access(result.page_token, user_id)
            if err is None:
                print_result(result)
                export_github_outputs(result)
                if result.secrets_update_needed:
                    print(
                        "::notice::トークンを更新しました。"
                        " INSTAGRAM_SECRETS_PAT が設定されていれば Secrets も自動更新されます。",
                        file=sys.stderr,
                    )
                return 0
            print(f"::warning::再取得トークンでも接続不可: {err}", file=sys.stderr)
        except (InstagramConfigError, InstagramAPIError) as exc:
            print(f"::warning::半永久トークン再取得に失敗: {exc}", file=sys.stderr)

    err = probe_media_access(token, user_id)
    if err is None:
        print("既存 INSTAGRAM_ACCESS_TOKEN で Instagram API に接続できました。")
        write_github_output("value", token)
        write_github_output("secrets_update_needed", "false")
        return 0

    print(f"::error::{err}", file=sys.stderr)
    print(f"::error::{TOKEN_HELP}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
