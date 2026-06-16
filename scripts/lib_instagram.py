"""Instagram Graph API helpers for portfolio diary sync."""

from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

GRAPH_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


class InstagramConfigError(Exception):
    """Missing or invalid configuration."""


class InstagramAPIError(Exception):
    """Graph API returned an error."""


def site_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (key not in os.environ or not os.environ[key].strip()):
            os.environ[key] = value


def load_meta_app_credentials() -> tuple[str, str]:
    app_id = os.environ.get("INSTAGRAM_APP_ID", "").strip()
    app_secret = os.environ.get("INSTAGRAM_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise InstagramConfigError(
            "INSTAGRAM_APP_ID と INSTAGRAM_APP_SECRET を config/instagram.env に設定してください。"
            "（Meta アプリ → 設定 → ベーシック）"
        )
    return app_id, app_secret


def load_config() -> dict[str, str]:
    root = site_root()
    load_env_file(root / "config" / "instagram.env")
    token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip().strip('"').strip("'")
    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip().strip('"').strip("'")
    if not token:
        raise InstagramConfigError(
            "INSTAGRAM_ACCESS_TOKEN が未設定です。config/instagram.env を作成してください。"
        )
    if not user_id:
        raise InstagramConfigError(
            "INSTAGRAM_USER_ID が未設定です。scripts/get_instagram_user_id.py を実行してください。"
        )
    return {
        "token": token,
        "user_id": user_id,
        "limit": os.environ.get("INSTAGRAM_SYNC_LIMIT", "50").strip() or "50",
    }


def app_access_token(app_id: str, app_secret: str) -> str:
    return f"{app_id}|{app_secret}"


def debug_token_info(token: str, app_id: str, app_secret: str) -> dict[str, Any]:
    data = graph_get(
        "debug_token",
        app_access_token(app_id, app_secret),
        {"input_token": token},
    )
    return data.get("data") or {}


def exchange_long_lived_user_token(
    token: str, app_id: str, app_secret: str
) -> tuple[str, int | None]:
    """短期／長期ユーザートークンを新しい長期ユーザートークンに交換する。"""
    resp = requests.get(
        f"{GRAPH_BASE}/oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": token,
        },
        timeout=60,
    )
    data = resp.json()
    if not resp.ok or "access_token" not in data:
        err = data.get("error", {})
        msg = err.get("message", resp.text)
        code = err.get("code", resp.status_code)
        raise InstagramAPIError(f"トークン延長エラー ({code}): {msg}")
    expires_in = data.get("expires_in")
    return str(data["access_token"]), int(expires_in) if expires_in is not None else None


def fetch_page_access_token(
    user_token: str, instagram_user_id: str | None = None
) -> tuple[str, str]:
    """長期ユーザートークンから、Instagram 連携済みページのアクセストークンを取得。"""
    accounts = graph_get(
        "me/accounts",
        user_token,
        {
            "fields": "name,access_token,instagram_business_account{id,username}",
        },
    )
    pages = accounts.get("data") or []
    if not pages:
        raise InstagramAPIError("管理できる Facebook ページが見つかりません。")

    preferred: list[dict[str, Any]] = []
    fallback: list[dict[str, Any]] = []
    for page in pages:
        ig = page.get("instagram_business_account") or {}
        if not ig.get("id"):
            continue
        fallback.append(page)
        if instagram_user_id and str(ig.get("id")) == str(instagram_user_id):
            preferred.append(page)

    chosen = (preferred or fallback or pages)[0]
    page_token = chosen.get("access_token")
    if not page_token:
        raise InstagramAPIError(
            f"ページ「{chosen.get('name', '?')}」のアクセストークンを取得できませんでした。"
        )
    ig = chosen.get("instagram_business_account") or {}
    label = ig.get("username") or chosen.get("name") or "page"
    return str(page_token), str(label)


def token_expires_within_days(info: dict[str, Any], days: int) -> bool:
    expires_at = info.get("expires_at")
    if expires_at in (None, "", 0, "0"):
        return False
    try:
        expiry = int(expires_at)
    except (TypeError, ValueError):
        return True
    if expiry <= 0:
        return False
    return expiry <= int(time.time()) + days * 86400


def format_token_expiry(info: dict[str, Any]) -> str:
    """debug_token の expires_at を人間向け文字列に。"""
    expires_at = info.get("expires_at")
    if expires_at in (None, "", 0, "0"):
        return "なし（無期限）"
    try:
        exp_dt = datetime.fromtimestamp(int(expires_at), tz=timezone.utc)
        return exp_dt.strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError, OSError):
        return "不明"


def is_non_expiring_token(info: dict[str, Any]) -> bool:
    expires_at = info.get("expires_at")
    return expires_at in (None, "", 0, "0")


def refresh_long_lived_user_token(
    user_token: str, app_id: str, app_secret: str
) -> tuple[str, int | None]:
    """長期ユーザートークンを再発行する（さらに約60日延長）。"""
    return exchange_long_lived_user_token(user_token, app_id, app_secret)


def refresh_instagram_access_token(
    token: str,
    app_id: str,
    app_secret: str,
    instagram_user_id: str | None = None,
    user_token: str | None = None,
) -> tuple[str, str]:
    """長期ユーザートークン経由でページトークンを更新する。"""
    base_user_token = (user_token or token).strip()
    long_lived, _ = exchange_long_lived_user_token(base_user_token, app_id, app_secret)
    page_token, label = fetch_page_access_token(long_lived, instagram_user_id)
    return page_token, label


def update_env_file_value(env_path: Path, key: str, value: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)
    prefix = f"{key}="
    replaced = False
    out: list[str] = []
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{prefix}{value}\n")
            replaced = True
        else:
            out.append(line if line.endswith("\n") else line + "\n")
    if not replaced:
        if out and not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.append(f"{prefix}{value}\n")
    env_path.write_text("".join(out), encoding="utf-8")


def graph_get(path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    q = {"access_token": token}
    if params:
        q.update(params)
    url = path if path.startswith("http") else f"{GRAPH_BASE}/{path.lstrip('/')}"
    resp = requests.get(url, params=q, timeout=60)
    data = resp.json()
    if not resp.ok or "error" in data:
        err = data.get("error", {})
        msg = err.get("message", resp.text)
        code = err.get("code", resp.status_code)
        raise InstagramAPIError(f"Graph API エラー ({code}): {msg}")
    return data


def discover_instagram_user_id(token: str) -> tuple[str, str]:
    """Return (instagram_user_id, human label)."""
    accounts = graph_get("me/accounts", token, {
        "fields": "name,instagram_business_account{id,username}",
    })
    pages = accounts.get("data") or []
    for page in pages:
        ig = page.get("instagram_business_account") or {}
        ig_id = ig.get("id")
        if ig_id:
            username = ig.get("username") or page.get("name") or ig_id
            return str(ig_id), f"@{username}"
    raise InstagramAPIError(
        "Instagram ビジネスアカウントが見つかりません。"
        "Facebook ページと Instagram の連携、およびトークンの権限を確認してください。"
    )


def verify_connection(token: str, user_id: str) -> dict[str, str]:
    data = graph_get(
        user_id,
        token,
        {"fields": "username,name"},
    )
    username = data.get("username") or data.get("name") or user_id
    return {"username": username, "user_id": user_id}


def probe_token_connection(
    token: str, user_id: str
) -> tuple[str | None, dict[str, str] | None]:
    """アカウントに接続できるかだけ検証（投稿0件でも成功）。"""
    if not token:
        return "トークンが空です", None
    try:
        account = verify_connection(token, user_id)
    except InstagramAPIError as exc:
        return str(exc), None
    return None, account


def probe_media_access(token: str, user_id: str, *, require_posts: bool = True) -> str | None:
    """Blog 同期に使えるか検証。問題なければ None、失敗理由を文字列で返す。"""
    err, account = probe_token_connection(token, user_id)
    if err is not None or account is None:
        return err
    try:
        items = iter_media(token, user_id, 1)
    except InstagramAPIError as exc:
        return str(exc)
    if not items and require_posts:
        username = account.get("username") or user_id
        return (
            f"@{username} から投稿を1件も取得できません。"
            " INSTAGRAM_USER_ID が @4mnion の ID か、トークン権限"
            "（instagram_basic, pages_show_list, pages_read_engagement）を確認してください。"
        )
    return None


def iter_media(token: str, user_id: str, max_items: int) -> list[dict[str, Any]]:
    fields = (
        "id,caption,media_type,media_url,thumbnail_url,timestamp,permalink,"
        "children{media_type,media_url}"
    )
    items: list[dict[str, Any]] = []
    path: str | None = f"{user_id}/media"
    params: dict[str, Any] | None = {"fields": fields, "limit": min(50, max_items)}

    while path and len(items) < max_items:
        data = graph_get(path, token, params)
        batch = data.get("data") or []
        items.extend(batch)
        if len(items) >= max_items:
            items = items[:max_items]
            break
        next_url = (data.get("paging") or {}).get("next")
        if not next_url:
            break
        path = next_url
        params = None

    return items


def media_image_url(item: dict[str, Any]) -> str | None:
    media_type = item.get("media_type")
    if media_type == "IMAGE":
        return item.get("media_url")
    if media_type == "CAROUSEL_ALBUM":
        children = (item.get("children") or {}).get("data") or []
        for child in children:
            if child.get("media_type") == "IMAGE" and child.get("media_url"):
                return child["media_url"]
        if children and children[0].get("media_url"):
            return children[0]["media_url"]
    if media_type in ("VIDEO", "REELS"):
        return item.get("thumbnail_url") or item.get("media_url")
    return item.get("media_url")


def parse_timestamp(ts: str) -> str:
    """表示用の日付（YYYY-MM-DD）。"""
    published = normalize_published_at(ts)
    return published[:10] if published else ""


def normalize_published_at(ts: str) -> str:
    """Instagram timestamp を UTC ISO（…Z）に正規化。並び順用。"""
    raw = (ts or "").strip()
    if not raw:
        return ""
    if raw.endswith("Z"):
        return raw
    if len(raw) >= 5 and raw[-5] in "+-" and raw[-3] != ":":
        # 2026-05-28T12:34:56+0000
        return raw[:-5] + "Z"
    return raw


def caption_title_body(caption: str | None) -> tuple[str, str]:
    text = (caption or "").strip()
    if not text:
        return "（無題）", ""
    lines = text.splitlines()
    title = lines[0].strip() or "（無題）"
    return title, text


def post_id_from_media(media_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", media_id)
    return f"ig-{safe}"


def image_filename(media_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", media_id)
    return f"{safe}.jpg"
