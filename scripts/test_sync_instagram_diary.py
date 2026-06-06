#!/usr/bin/env python3
"""Instagram Diary 同期のマージ・並び順テスト。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_instagram_diary import merge_diary_posts


def post(ig_id: str, title: str, date: str, published_at: str) -> dict:
    return {
        "id": f"ig-{ig_id}",
        "instagramMediaId": ig_id,
        "title": title,
        "date": date,
        "publishedAt": published_at,
        "body": title,
        "image": f"images/diary/{ig_id}.jpg",
    }


class MergeDiaryPostsTests(unittest.TestCase):
    def test_preserves_instagram_order_for_same_day(self) -> None:
        """同日投稿でも API 返却順（新しい順）を維持する。"""
        existing: list[dict] = []
        fresh = [
            post("200", "newer", "2026-06-06", "2026-06-06T15:00:00Z"),
            post("100", "older", "2026-06-06", "2026-06-06T09:00:00Z"),
        ]
        window = [
            ("200", "2026-06-06T15:00:00Z"),
            ("100", "2026-06-06T09:00:00Z"),
        ]
        merged = merge_diary_posts(existing, fresh, window)
        self.assertEqual(
            [p["instagramMediaId"] for p in merged],
            ["200", "100"],
        )

    def test_keeps_legacy_outside_window(self) -> None:
        existing = [
            post("old", "archive", "2026-05-01", "2026-05-01T10:00:00Z"),
        ]
        fresh = [post("new", "latest", "2026-06-06", "2026-06-06T12:00:00Z")]
        window = [("new", "2026-06-06T12:00:00Z")]
        merged = merge_diary_posts(existing, fresh, window)
        self.assertEqual(
            [p["instagramMediaId"] for p in merged],
            ["new", "old"],
        )

    def test_deletes_removed_recent_post(self) -> None:
        existing = [
            post("gone", "deleted", "2026-06-06", "2026-06-06T08:00:00Z"),
            post("old", "archive", "2026-05-01", "2026-05-01T10:00:00Z"),
        ]
        fresh = [post("stay", "latest", "2026-06-06", "2026-06-06T12:00:00Z")]
        window = [("stay", "2026-06-06T12:00:00Z")]
        merged = merge_diary_posts(existing, fresh, window)
        self.assertEqual([p["instagramMediaId"] for p in merged], ["stay", "old"])

    def test_keeps_existing_when_video_skipped_in_window(self) -> None:
        existing = [
            post("video", "was-synced", "2026-06-05", "2026-06-05T18:00:00Z"),
        ]
        fresh: list[dict] = []
        window = [
            ("video", "2026-06-05T18:00:00Z"),
            ("img", "2026-06-05T12:00:00Z"),
        ]
        merged = merge_diary_posts(existing, fresh, window)
        self.assertEqual([p["instagramMediaId"] for p in merged], ["video"])


if __name__ == "__main__":
    raise SystemExit(unittest.main())
