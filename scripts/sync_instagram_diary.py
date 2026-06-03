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

    posts, warnings = build_posts(
        media_items,
        images_dir,
        dry_run=args.dry_run,
        skip_video=not args.keep_video,
    )

    payload = {"posts": posts, "syncedFrom": "instagram", "syncLimit": limit}

    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        for w in warnings:
            print(f"注意: {w}", file=sys.stderr)
        print(f"\n[dry-run] 取得 {len(media_items)} 件 → 反映 {len(posts)} 件", file=sys.stderr)
        return 0

    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    removed = prune_orphan_images(images_dir, posts, dry_run=False)

    print(f"同期完了: {len(posts)} 件を {data_path.relative_to(root)} に保存")
    if removed:
        print(f"不要画像を {removed} 件削除")
    for w in warnings:
        print(f"注意: {w}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
