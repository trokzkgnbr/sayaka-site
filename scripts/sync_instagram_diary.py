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


def build_posts(
    media_items: list,
    images_dir: Path,
    dry_run: bool,
    skip_video: bool,
) -> tuple[list[dict], list[str]]:
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

        date = parse_timestamp(item.get("timestamp") or "")
        if not date:
            warnings.append(f"日付不明のためスキップ: {media_id}")
            continue

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
            "title": title,
            "body": body,
            "image": rel_image,
            "instagramMediaId": str(media_id),
        })

    posts.sort(key=lambda p: (p["date"], p.get("instagramMediaId", "")), reverse=True)
    return posts, warnings


def load_existing_posts(data_path: Path) -> list[dict]:
    if not data_path.is_file():
        return []
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    posts = data.get("posts")
    return posts if isinstance(posts, list) else []


def merge_diary_posts(existing: list[dict], fresh_from_ig: list[dict]) -> list[dict]:
    """
    直近 sync 枠（Instagram から取得した件）だけ追加・更新・削除する。
    それより古い投稿（51件目以降相当）は Instagram から消えても残す。
    """
    fresh_by_ig_id: dict[str, dict] = {}
    for post in fresh_from_ig:
        ig_id = post.get("instagramMediaId")
        if ig_id:
            fresh_by_ig_id[str(ig_id)] = post

    fresh_ids = set(fresh_by_ig_id.keys())
    oldest_sync_date = (
        min(p["date"] for p in fresh_from_ig) if fresh_from_ig else None
    )

    legacy: list[dict] = []
    for post in existing:
        ig_id = post.get("instagramMediaId")
        if not ig_id:
            legacy.append(post)
            continue
        if str(ig_id) in fresh_ids:
            continue
        if oldest_sync_date and post.get("date", "") < oldest_sync_date:
            legacy.append(post)

    merged = list(fresh_from_ig) + legacy
    merged.sort(
        key=lambda p: (p.get("date", ""), p.get("instagramMediaId", "")),
        reverse=True,
    )

    seen_ids: set[str] = set()
    result: list[dict] = []
    for post in merged:
        post_id = post.get("id")
        if not post_id or post_id in seen_ids:
            continue
        seen_ids.add(post_id)
        result.append(post)
    return result


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

    fresh_posts, warnings = build_posts(
        media_items,
        images_dir,
        dry_run=args.dry_run,
        skip_video=not args.keep_video,
    )

    existing_posts = load_existing_posts(data_path)
    merged_posts = merge_diary_posts(existing_posts, fresh_posts)

    fresh_ids = {
        str(p["instagramMediaId"])
        for p in fresh_posts
        if p.get("instagramMediaId")
    }
    deleted_recent = 0
    oldest_sync_date = min((p["date"] for p in fresh_posts), default=None)
    if oldest_sync_date:
        for post in existing_posts:
            ig_id = post.get("instagramMediaId")
            if not ig_id:
                continue
            if str(ig_id) in fresh_ids:
                continue
            if post.get("date", "") >= oldest_sync_date:
                deleted_recent += 1

    payload = {
        "posts": merged_posts,
        "syncedFrom": "instagram",
        "syncLimit": limit,
        "syncRecentManaged": len(fresh_posts),
    }

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        for w in warnings:
            print(f"注意: {w}", file=sys.stderr)
        print(
            f"\n[dry-run] Instagram {len(fresh_posts)} 件 → 合計 {len(merged_posts)} 件"
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
        f"同期完了: 直近 {len(fresh_posts)} 件を反映、合計 {len(merged_posts)} 件"
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
