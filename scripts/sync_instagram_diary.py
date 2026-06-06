#!/usr/bin/env python3
"""
Instagram の投稿を data/diary.json と images/diary/ に同期する。

使い方:
  bash scripts/run_sync.sh
  bash scripts/run_sync.sh --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

from lib_instagram import (
    InstagramAPIError,
    InstagramConfigError,
    caption_title_body,
    image_filename,
    iter_media,
    load_config,
    media_image_url,
    normalize_published_at,
    parse_timestamp,
    post_id_from_media,
    site_root,
)


def download_image(url: str, dest: Path, dry_run: bool) -> None:
    if dry_run:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    dest.write_bytes(resp.content)


def extract_managed_window(media_items: list) -> list[tuple[str, str]]:
    """API 返却順（新しい順）の (media_id, publishedAt)。"""
    window: list[tuple[str, str]] = []
    for item in media_items:
        media_id = item.get("id")
        if not media_id:
            continue
        published = normalize_published_at(item.get("timestamp") or "")
        if not published:
            continue
        window.append((str(media_id), published))
    return window


def post_published_at(post: dict) -> str:
    published = post.get("publishedAt")
    if published:
        return str(published)
    date = post.get("date", "")
    return f"{date}T00:00:00Z" if date else ""


def post_display_date(post: dict) -> str:
    published = post.get("publishedAt")
    if published:
        return str(published)[:10]
    return str(post.get("date", ""))


def oldest_managed_date(managed_window: list[tuple[str, str]]) -> str | None:
    if not managed_window:
        return None
    return min(published[:10] for _, published in managed_window)


def is_outside_managed_window(post: dict, managed_window: list[tuple[str, str]]) -> bool:
    """取得枠より古い日付の投稿だけ Blog に残す。"""
    oldest_date = oldest_managed_date(managed_window)
    if not oldest_date:
        return False
    return post_display_date(post) < oldest_date


def build_posts(
    media_items: list,
    images_dir: Path,
    dry_run: bool,
    skip_video: bool,
) -> tuple[list[dict], list[str]]:
    """Instagram API 順を保ったまま Blog 用投稿を組み立てる。"""
    posts: list[dict] = []
    warnings: list[str] = []

    for item in media_items:
        media_id = item.get("id")
        if not media_id:
            continue

        media_type = item.get("media_type", "")
        if skip_video and media_type in ("VIDEO", "REELS"):
            warnings.append(f"動画のためスキップ: {media_id}")
            continue

        image_url = media_image_url(item)
        if not image_url:
            warnings.append(f"画像URLなしのためスキップ: {media_id} ({media_type})")
            continue

        published_at = normalize_published_at(item.get("timestamp") or "")
        if not published_at:
            warnings.append(f"日付不明のためスキップ: {media_id}")
            continue

        date = parse_timestamp(item.get("timestamp") or "")
        title, body = caption_title_body(item.get("caption"))
        fname = image_filename(str(media_id))
        rel_image = f"images/diary/{fname}"
        dest = images_dir / fname

        try:
            download_image(image_url, dest, dry_run)
        except requests.RequestException as exc:
            warnings.append(f"画像ダウンロード失敗 {media_id}: {exc}")
            continue

        posts.append({
            "id": post_id_from_media(str(media_id)),
            "date": date,
            "publishedAt": published_at,
            "title": title,
            "body": body,
            "image": rel_image,
            "instagramMediaId": str(media_id),
        })

    return posts, warnings


def load_existing_data(data_path: Path) -> tuple[list[dict], dict]:
    if not data_path.is_file():
        return [], {}
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return [], {}
    if not isinstance(data, dict):
        return [], {}
    posts = data.get("posts")
    posts = posts if isinstance(posts, list) else []
    meta = {k: v for k, v in data.items() if k != "posts"}
    return posts, meta


def posts_signature(posts: list[dict]) -> str:
    """配列順序を含めて変更検知する。"""
    return json.dumps(posts, ensure_ascii=False)


def merge_diary_posts(
    existing: list[dict],
    fresh_posts: list[dict],
    managed_window: list[tuple[str, str]],
) -> list[dict]:
    """
    Instagram の取得順を保ちつつマージする。

    - managed_window: API が返した直近 N 件（動画含む）の ID 順
    - 枠内で Instagram から消えた投稿は Blog からも削除
    - 枠内の動画など同期対象外は既存 Blog 投稿を維持
    - 枠より古い投稿は Instagram から消えても Blog に残す
    """
    fresh_by_id = {
        str(p["instagramMediaId"]): p
        for p in fresh_posts
        if p.get("instagramMediaId")
    }
    existing_by_id = {
        str(p["instagramMediaId"]): p
        for p in existing
        if p.get("instagramMediaId")
    }
    seen_ids = {ig_id for ig_id, _ in managed_window}

    legacy: list[dict] = []
    for post in existing:
        ig_id = post.get("instagramMediaId")
        if not ig_id:
            legacy.append(post)
            continue
        ig_id = str(ig_id)
        if ig_id in seen_ids:
            continue
        if is_outside_managed_window(post, managed_window):
            legacy.append(post)

    ordered: list[dict] = []
    seen_post_ids: set[str] = set()

    for ig_id, _ in managed_window:
        post = fresh_by_id.get(ig_id) or existing_by_id.get(ig_id)
        if not post:
            continue
        post_id = post.get("id")
        if not post_id or post_id in seen_post_ids:
            continue
        seen_post_ids.add(post_id)
        ordered.append(post)

    for post in legacy:
        post_id = post.get("id")
        if not post_id or post_id in seen_post_ids:
            continue
        seen_post_ids.add(post_id)
        ordered.append(post)

    return ordered


def count_deleted_in_managed_window(
    existing: list[dict],
    managed_window: list[tuple[str, str]],
) -> int:
    if not managed_window:
        return 0
    seen_ids = {ig_id for ig_id, _ in managed_window}
    deleted = 0
    for post in existing:
        ig_id = post.get("instagramMediaId")
        if not ig_id:
            continue
        if str(ig_id) in seen_ids:
            continue
        if not is_outside_managed_window(post, managed_window):
            deleted += 1
    return deleted


def prune_orphan_images(images_dir: Path, posts: list[dict], dry_run: bool) -> int:
    keep = {Path(p["image"]).name for p in posts}
    removed = 0
    if not images_dir.is_dir():
        return 0
    for path in images_dir.glob("*.jpg"):
        if path.name not in keep:
            if not dry_run:
                path.unlink()
            removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Instagram → Diary 同期")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="JSON・画像を書き込まず、取得内容だけ表示",
    )
    parser.add_argument(
        "--keep-video",
        action="store_true",
        help="動画・リールもサムネイルがあれば取り込む（既定はスキップ）",
    )
    args = parser.parse_args()

    root = site_root()
    data_path = root / "data" / "diary.json"
    images_dir = root / "images" / "diary"

    try:
        cfg = load_config()
        limit = max(1, min(200, int(cfg["limit"])))
    except (InstagramConfigError, ValueError) as exc:
        print(f"設定エラー: {exc}", file=sys.stderr)
        return 1

    try:
        media_items = iter_media(cfg["token"], cfg["user_id"], limit)
    except InstagramAPIError as exc:
        print(f"API エラー: {exc}", file=sys.stderr)
        return 1

    managed_window = extract_managed_window(media_items)
    fresh_posts, warnings = build_posts(
        media_items,
        images_dir,
        dry_run=args.dry_run,
        skip_video=not args.keep_video,
    )

    existing_posts, existing_meta = load_existing_data(data_path)
    merged_posts = merge_diary_posts(existing_posts, fresh_posts, managed_window)
    content_changed = posts_signature(existing_posts) != posts_signature(merged_posts)
    deleted_recent = count_deleted_in_managed_window(existing_posts, managed_window)

    payload = {
        "posts": merged_posts,
        "syncedFrom": "instagram",
        "syncLimit": limit,
        "syncWindowSize": len(managed_window),
        "syncRecentManaged": len(fresh_posts),
    }
    if content_changed or deleted_recent or not existing_meta.get("lastSyncedAt"):
        payload["lastSyncedAt"] = datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    else:
        payload["lastSyncedAt"] = existing_meta["lastSyncedAt"]

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        for w in warnings:
            print(f"注意: {w}", file=sys.stderr)
        print(
            f"\n[dry-run] Instagram 同期 {len(fresh_posts)} 件"
            f"（取得枠 {len(managed_window)} 件）→ 合計 {len(merged_posts)} 件"
            f"（{len(merged_posts) - len(fresh_posts)} 件は古い投稿として保持）",
            file=sys.stderr,
        )
        return 0

    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    removed = prune_orphan_images(images_dir, merged_posts, dry_run=False)

    print(
        f"同期完了: 直近 {len(fresh_posts)} 件を反映"
        f"（取得枠 {len(managed_window)} 件）、合計 {len(merged_posts)} 件"
        f"（{data_path.relative_to(root)}）"
    )
    if deleted_recent:
        print(f"直近枠から削除（Instagram 側で消えた投稿）: {deleted_recent} 件")
    if removed:
        print(f"不要画像を {removed} 件削除")
    for w in warnings:
        print(f"注意: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
