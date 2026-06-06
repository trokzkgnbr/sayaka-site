#!/usr/bin/env python3
"""
同期後の data/diary.json を検証する。

Instagram から消えた投稿が Blog に残っていないか、managedInstagramIds と照合する。
同期スクリプト内の verify に加え、書き込み後の JSON でも再チェックする。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_instagram_diary import should_keep_unmanaged_post, site_root


def main() -> int:
    data_path = site_root() / "data" / "diary.json"
    if not data_path.is_file():
        print("data/diary.json がありません", file=sys.stderr)
        return 1

    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"diary.json の読み込みに失敗: {exc}", file=sys.stderr)
        return 1

    posts = data.get("posts")
    if not isinstance(posts, list):
        print("posts が配列ではありません", file=sys.stderr)
        return 1

    managed_ids = data.get("managedInstagramIds")
    if not isinstance(managed_ids, list):
        print(
            "managedInstagramIds がありません。同期スクリプトを更新して再実行してください。",
            file=sys.stderr,
        )
        return 1

    managed_window = [(str(ig_id), "") for ig_id in managed_ids]
    limit_reached = bool(data.get("syncLimitReached"))
    seen_ids = {str(ig_id) for ig_id in managed_ids}

    errors: list[str] = []
    for post in posts:
        ig_id = post.get("instagramMediaId")
        if not ig_id:
            continue
        ig_id = str(ig_id)
        if ig_id in seen_ids:
            continue
        if should_keep_unmanaged_post(post, managed_window, limit_reached):
            continue
        title = post.get("title", post.get("id", "?"))
        errors.append(
            f"Blog に残っているが Instagram 取得枠に無い投稿: {title} (instagramMediaId={ig_id})"
        )

    if errors:
        for msg in errors:
            print(f"検証エラー: {msg}", file=sys.stderr)
        return 1

    print(
        f"検証 OK: {len(posts)} 件"
        f"（取得枠 {len(managed_ids)} 件、上限到達={limit_reached}）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
