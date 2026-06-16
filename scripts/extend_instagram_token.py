#!/usr/bin/env python3
"""Instagram ページトークンを長期化・更新する（後方互換ラッパー）。"""

from __future__ import annotations

import argparse
import os
import sys

from maintain_instagram_tokens import maintain_from_env, print_result, write_env_tokens
from lib_instagram import (
    InstagramAPIError,
    InstagramConfigError,
    probe_media_access,
    site_root,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Instagram アクセストークンを延長する")
    parser.add_argument(
        "--if-needed",
        action="store_true",
        help="無期限ページトークンかつユーザートークンに余裕があればスキップ",
    )
    parser.add_argument("--force", action="store_true", help="期限に関わらず延長を試す")
    parser.add_argument("--dry-run", action="store_true", help="instagram.env は書き換えない")
    parser.add_argument("--export-env", action="store_true", help="新トークンを stdout に出す（CI 用）")
    args = parser.parse_args()

    env_path = site_root() / "config" / "instagram.env"

    try:
        result = maintain_from_env(
            force_user_refresh=args.force,
            if_needed=args.if_needed and not args.force,
        )
    except (InstagramConfigError, InstagramAPIError) as exc:
        print(f"× {exc}", file=sys.stderr)
        return 1

    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    if user_id:
        err = probe_media_access(result.page_token, user_id)
        if err:
            print(f"× {err}", file=sys.stderr)
            return 1

    print_result(result)

    if args.export_env:
        print(f"INSTAGRAM_ACCESS_TOKEN={result.page_token}")
        print(f"INSTAGRAM_USER_ACCESS_TOKEN={result.user_token}")
        return 0

    if args.dry_run:
        print("（--dry-run のため instagram.env は変更していません）")
        return 0

    if env_path.is_file():
        write_env_tokens(env_path, result)
        print(f"保存しました: {env_path}")
        if result.secrets_update_needed:
            print(
                "GitHub Secrets の INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_USER_ACCESS_TOKEN"
                " も同じ値に更新してください。"
            )
    else:
        print("instagram.env がないため、新トークンは手動で保存してください。", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
