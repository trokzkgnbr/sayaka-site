#!/usr/bin/env python3
"""Instagram ページトークンを長期化・更新する（60日切れ対策）。"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from lib_instagram import (
    InstagramAPIError,
    InstagramConfigError,
    debug_token_info,
    load_env_file,
    load_meta_app_credentials,
    refresh_instagram_access_token,
    site_root,
    token_expires_within_days,
    update_env_file_value,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Instagram アクセストークンを延長する")
    parser.add_argument(
        "--if-needed",
        action="store_true",
        help="有効期限が14日以内のときだけ延長する（ページ無期限トークンはスキップ）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="期限に関わらず延長を試す",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="instagram.env は書き換えない",
    )
    parser.add_argument(
        "--export-env",
        action="store_true",
        help="新トークンを INSTAGRAM_ACCESS_TOKEN=... 形式で stdout に出す（CI 用）",
    )
    args = parser.parse_args()

    import os

    root = site_root()
    env_path = root / "config" / "instagram.env"
    load_env_file(env_path)

    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    if not token:
        print(
            "INSTAGRAM_ACCESS_TOKEN を config/instagram.env に設定してください。",
            file=sys.stderr,
        )
        return 1

    try:
        app_id, app_secret = load_meta_app_credentials()
    except InstagramConfigError as exc:
        print(f"× {exc}", file=sys.stderr)
        return 1

    try:
        info = debug_token_info(token, app_id, app_secret)
    except InstagramAPIError as exc:
        print(f"× トークン確認: {exc}", file=sys.stderr)
        return 1

    if not info.get("is_valid", True):
        print("× トークンが無効です。Graph API エクスプローラで取り直してください。", file=sys.stderr)
        return 1

    token_type = info.get("type", "不明")
    expires_at = info.get("expires_at")
    if expires_at not in (None, "", 0, "0"):
        try:
            exp_dt = datetime.fromtimestamp(int(expires_at), tz=timezone.utc)
            print(f"現在のトークン種別: {token_type} / 有効期限(UTC): {exp_dt.isoformat()}")
        except (TypeError, ValueError, OSError):
            print(f"現在のトークン種別: {token_type}")
    else:
        print(f"現在のトークン種別: {token_type} / 有効期限: なし（ページ無期限の可能性）")

    if args.if_needed and not args.force:
        if not token_expires_within_days(info, 14):
            print("延長不要: 有効期限まで14日以上あるか、無期限トークンです。")
            return 0

    try:
        new_token, label = refresh_instagram_access_token(
            token, app_id, app_secret, user_id or None
        )
    except InstagramAPIError as exc:
        print(f"× {exc}", file=sys.stderr)
        if token_type == "PAGE":
            print(
                "\nヒント: ページトークンだけでは延長できない場合があります。"
                "エクスプローラで「3. ユーザーアクセストークン」を取得し、"
                "延長後に「1. ページアクセストークン」を取り直してから再実行してください。",
                file=sys.stderr,
            )
        return 1

    print(f"延長成功: ページトークンを更新しました（{label}）")

    if args.export_env:
        print(f"INSTAGRAM_ACCESS_TOKEN={new_token}")
        return 0

    if args.dry_run:
        print("（--dry-run のため instagram.env は変更していません）")
        return 0

    if env_path.is_file():
        update_env_file_value(env_path, "INSTAGRAM_ACCESS_TOKEN", new_token)
        print(f"保存しました: {env_path}")
        print("GitHub を使っている場合は Secrets の INSTAGRAM_ACCESS_TOKEN も同じ値に更新してください。")
    else:
        print("instagram.env がないため、新トークンは手動で保存してください。", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
