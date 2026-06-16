#!/usr/bin/env python3
"""
Instagram トークンを半永久運用向けに整える。

- INSTAGRAM_USER_ACCESS_TOKEN（長期ユーザートークン）を約30日切れ前に自動延長
- 長期ユーザートークンからページトークンを毎回再取得（多くの場合 Expires: Never）
- 更新があれば instagram.env / GitHub Secrets に書き戻し可能
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from lib_instagram import (
    InstagramAPIError,
    InstagramConfigError,
    debug_token_info,
    fetch_page_access_token,
    format_token_expiry,
    is_non_expiring_token,
    load_env_file,
    load_meta_app_credentials,
    probe_media_access,
    probe_token_connection,
    refresh_long_lived_user_token,
    site_root,
    token_expires_within_days,
    update_env_file_value,
)

DEFAULT_USER_REFRESH_DAYS = 30


@dataclass
class TokenMaintenanceResult:
    page_token: str
    user_token: str
    page_label: str
    user_token_refreshed: bool
    page_token_derived: bool
    page_expires: str
    user_expires: str
    page_token_type: str
    user_token_type: str
    secrets_update_needed: bool
    used_user_token_path: bool


def write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not path:
        return
    delimiter = f"{name.upper()}_EOF"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")


def resolve_user_access_token(
    user_access_token: str,
    access_token: str,
    app_id: str,
    app_secret: str,
) -> str:
    """Secret / env から使える長期ユーザートークンを決める。"""
    explicit = user_access_token.strip().strip('"').strip("'")
    if explicit:
        info = debug_token_info(explicit, app_id, app_secret)
        if info.get("is_valid", True):
            return explicit
        raise InstagramAPIError(
            "INSTAGRAM_USER_ACCESS_TOKEN が無効です。D-1〜D-2 で取り直してください。"
        )

    fallback = access_token.strip().strip('"').strip("'")
    if not fallback:
        raise InstagramConfigError(
            "INSTAGRAM_USER_ACCESS_TOKEN または INSTAGRAM_ACCESS_TOKEN が必要です。"
        )

    info = debug_token_info(fallback, app_id, app_secret)
    if not info.get("is_valid", True):
        raise InstagramAPIError("INSTAGRAM_ACCESS_TOKEN が無効です。")

    token_type = str(info.get("type", "")).upper()
    if token_type == "USER":
        refreshed, _ = refresh_long_lived_user_token(fallback, app_id, app_secret)
        return refreshed

    raise InstagramConfigError(
        "INSTAGRAM_USER_ACCESS_TOKEN が未設定で、ACCESS_TOKEN はページトークンです。"
        " docs/INSTAGRAM_DIARY_SETUP.md の D-2.6（半永久設定）を実行してください。"
    )


def maintain_instagram_tokens(
    *,
    user_access_token: str,
    page_access_token: str,
    instagram_user_id: str,
    app_id: str,
    app_secret: str,
    refresh_user_within_days: int = DEFAULT_USER_REFRESH_DAYS,
    force_user_refresh: bool = False,
) -> TokenMaintenanceResult:
    """
    長期ユーザートークンを延長し、ページトークンを再取得する。

    Meta の仕様上、ユーザートークンは最長約60日だが同期のたびに延長可能。
    長期ユーザートークンから取得したページトークンは多くの場合無期限（Expires: Never）。
    """
    user_token = resolve_user_access_token(
        user_access_token, page_access_token, app_id, app_secret
    )
    user_info = debug_token_info(user_token, app_id, app_secret)
    user_refreshed = False

    if force_user_refresh or token_expires_within_days(user_info, refresh_user_within_days):
        user_token, _ = refresh_long_lived_user_token(user_token, app_id, app_secret)
        user_refreshed = True
        user_info = debug_token_info(user_token, app_id, app_secret)

    page_token, page_label = fetch_page_access_token(user_token, instagram_user_id)
    page_info = debug_token_info(page_token, app_id, app_secret)

    stored_page = page_access_token.strip().strip('"').strip("'")
    stored_user = user_access_token.strip().strip('"').strip("'")
    secrets_update_needed = (
        user_refreshed
        or page_token != stored_page
        or user_token != stored_user
    )

    return TokenMaintenanceResult(
        page_token=page_token,
        user_token=user_token,
        page_label=page_label,
        user_token_refreshed=user_refreshed,
        page_token_derived=True,
        page_expires=format_token_expiry(page_info),
        user_expires=format_token_expiry(user_info),
        page_token_type=str(page_info.get("type", "不明")),
        user_token_type=str(user_info.get("type", "不明")),
        secrets_update_needed=secrets_update_needed,
        used_user_token_path=True,
    )


def maintain_from_env(
    *,
    refresh_user_within_days: int = DEFAULT_USER_REFRESH_DAYS,
    force_user_refresh: bool = False,
    if_needed: bool = False,
) -> TokenMaintenanceResult:
    root = site_root()
    env_path = root / "config" / "instagram.env"
    load_env_file(env_path)

    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    if not user_id:
        raise InstagramConfigError("INSTAGRAM_USER_ID が未設定です。")

    app_id, app_secret = load_meta_app_credentials()
    user_access = os.environ.get("INSTAGRAM_USER_ACCESS_TOKEN", "")
    page_access = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

    user_info_before: dict | None = None
    explicit_user = user_access.strip().strip('"').strip("'")
    if explicit_user and if_needed and not force_user_refresh:
        user_info_before = debug_token_info(explicit_user, app_id, app_secret)
        if not token_expires_within_days(user_info_before, refresh_user_within_days):
            page_token = page_access.strip().strip('"').strip("'")
            if page_token:
                err, _ = probe_token_connection(page_token, user_id)
                if err is None:
                    page_info = debug_token_info(page_token, app_id, app_secret)
                    if is_non_expiring_token(page_info):
                        return TokenMaintenanceResult(
                            page_token=page_token,
                            user_token=explicit_user,
                            page_label="existing",
                            user_token_refreshed=False,
                            page_token_derived=False,
                            page_expires=format_token_expiry(page_info),
                            user_expires=format_token_expiry(user_info_before),
                            page_token_type=str(page_info.get("type", "不明")),
                            user_token_type=str(user_info_before.get("type", "不明")),
                            secrets_update_needed=False,
                            used_user_token_path=False,
                        )

    return maintain_instagram_tokens(
        user_access_token=user_access,
        page_access_token=page_access,
        instagram_user_id=user_id,
        app_id=app_id,
        app_secret=app_secret,
        refresh_user_within_days=refresh_user_within_days,
        force_user_refresh=force_user_refresh,
    )


def print_result(result: TokenMaintenanceResult) -> None:
    print(
        f"ページトークン: {result.page_label} / 種別={result.page_token_type}"
        f" / 期限={result.page_expires}"
    )
    print(
        f"ユーザートークン: 種別={result.user_token_type} / 期限={result.user_expires}"
    )
    if result.user_token_refreshed:
        print("ユーザートークンを延長しました（約60日延長）。")
    if result.page_expires.startswith("なし"):
        print("ページトークンは無期限です（Meta の Debugger で Expires: Never）。")
    elif not result.used_user_token_path:
        print("既存の無期限ページトークンをそのまま使用します。")


def write_env_tokens(env_path: Path, result: TokenMaintenanceResult) -> None:
    if not env_path.is_file():
        return
    update_env_file_value(env_path, "INSTAGRAM_ACCESS_TOKEN", result.page_token)
    update_env_file_value(env_path, "INSTAGRAM_USER_ACCESS_TOKEN", result.user_token)


def push_github_secrets(result: TokenMaintenanceResult, repo: str) -> int:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("::warning::GH_TOKEN が無いため Secrets は更新しません。", file=sys.stderr)
        return 0

    from push_github_secret import encrypt, api  # noqa: PLC0415

    gh_token = token
    pk = api("GET", f"https://api.github.com/repos/{repo}/actions/secrets/public-key", gh_token)
    updates = {
        "INSTAGRAM_ACCESS_TOKEN": result.page_token,
        "INSTAGRAM_USER_ACCESS_TOKEN": result.user_token,
    }
    for name, value in updates.items():
        body = {
            "encrypted_value": encrypt(pk["key"], value),
            "key_id": pk["key_id"],
        }
        import json  # noqa: PLC0415
        import urllib.request  # noqa: PLC0415

        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
            data=json.dumps(body).encode(),
            method="PUT",
            headers={
                "Authorization": f"Bearer {gh_token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        urllib.request.urlopen(req)
        print(f"GitHub Secret 更新: {name}")

    return 0


def export_github_outputs(result: TokenMaintenanceResult) -> None:
    write_github_output("value", result.page_token)
    write_github_output("user_token", result.user_token)
    write_github_output(
        "secrets_update_needed",
        "true" if result.secrets_update_needed else "false",
    )
    write_github_output(
        "user_refreshed",
        "true" if result.user_token_refreshed else "false",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Instagram トークンを半永久運用向けに整える")
    parser.add_argument(
        "--if-needed",
        action="store_true",
        help="無期限ページトークンかつユーザートークンに余裕があればスキップ",
    )
    parser.add_argument("--force", action="store_true", help="期限に関わらずユーザートークンを延長")
    parser.add_argument("--write-env", action="store_true", help="config/instagram.env を更新")
    parser.add_argument("--export-env", action="store_true", help="新トークンを stdout に出力（CI 用）")
    parser.add_argument("--export-github-output", action="store_true", help="GITHUB_OUTPUT に書く")
    parser.add_argument(
        "--push-github-secrets",
        action="store_true",
        help="GH_TOKEN があれば Secrets を更新",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPO", "trokzkgnbr/sayaka-site"),
    )
    args = parser.parse_args()

    root = site_root()
    env_path = root / "config" / "instagram.env"
    load_env_file(env_path)

    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    if not user_id:
        print("::error::INSTAGRAM_USER_ID が未設定です。" if args.export_github_output else "INSTAGRAM_USER_ID が未設定です。", file=sys.stderr)
        return 1

    try:
        result = maintain_from_env(
            force_user_refresh=args.force,
            if_needed=args.if_needed,
        )
    except (InstagramConfigError, InstagramAPIError) as exc:
        msg = str(exc)
        print(f"::error::{msg}" if args.export_github_output else f"× {msg}", file=sys.stderr)
        return 1

    err, account = probe_token_connection(result.page_token, user_id)
    if err is not None:
        print(f"::error::{err}" if args.export_github_output else f"× {err}", file=sys.stderr)
        return 1

    post_err = probe_media_access(result.page_token, user_id, require_posts=True)
    if post_err is not None:
        username = (account or {}).get("username") or user_id
        msg = (
            f"@{username} の Instagram API 投稿が 0 件です。"
            " Blog の既存データは維持します。@4mnion に画像投稿があるか、"
            " Meta アプリの Instagram テスター設定を確認してください。"
        )
        if args.export_github_output:
            print(f"::warning::{msg}", file=sys.stderr)
        else:
            print(f"注意: {msg}", file=sys.stderr)

    print_result(result)

    if args.export_env:
        print(f"INSTAGRAM_ACCESS_TOKEN={result.page_token}")
        print(f"INSTAGRAM_USER_ACCESS_TOKEN={result.user_token}")
    if args.export_github_output:
        export_github_outputs(result)
    if args.write_env:
        write_env_tokens(env_path, result)
        print(f"保存しました: {env_path}")
    if args.push_github_secrets and result.secrets_update_needed:
        try:
            push_github_secrets(result, args.repo)
        except Exception as exc:  # noqa: BLE001
            print(f"::warning::GitHub Secrets 更新に失敗: {exc}", file=sys.stderr)

    if result.secrets_update_needed and not args.push_github_secrets:
        print(
            "Secrets の INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_USER_ACCESS_TOKEN を"
            " 上記の値に更新するか、INSTAGRAM_SECRETS_PAT を設定して自動更新してください。"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
