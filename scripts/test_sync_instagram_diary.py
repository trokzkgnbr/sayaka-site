#!/usr/bin/env python3
"""Instagram Diary 同期のマージ・削除・整合性テスト。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sync_instagram_diary import (
    find_undeleted_posts,
    merge_diary_posts,
    verify_merged_posts,
)


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
        merged = merge_diary_posts(existing, fresh, window, limit_reached=False)
        self.assertEqual(
            [p["instagramMediaId"] for p in merged],
            ["200", "100"],
        )

    def test_keeps_legacy_outside_window_when_limit_reached(self) -> None:
        existing = [
            post("old", "archive", "2026-05-01", "2026-05-01T10:00:00Z"),
        ]
        fresh = [post("new", "latest", "2026-06-06", "2026-06-06T12:00:00Z")]
        window = [("new", "2026-06-06T12:00:00Z")]
        merged = merge_diary_posts(existing, fresh, window, limit_reached=True)
        self.assertEqual(
            [p["instagramMediaId"] for p in merged],
            ["new", "old"],
        )

    def test_deletes_removed_recent_post_when_limit_reached(self) -> None:
        existing = [
            post("gone", "deleted", "2026-06-06", "2026-06-06T08:00:00Z"),
            post("old", "archive", "2026-05-01", "2026-05-01T10:00:00Z"),
        ]
        fresh = [post("stay", "latest", "2026-06-06", "2026-06-06T12:00:00Z")]
        window = [("stay", "2026-06-06T12:00:00Z")]
        merged = merge_diary_posts(existing, fresh, window, limit_reached=True)
        self.assertEqual([p["instagramMediaId"] for p in merged], ["stay", "old"])

    def test_deletes_removed_post_when_all_instagram_fetched(self) -> None:
        """取得件数が上限未満 = 全投稿取得済み。消えた投稿は日付に関係なく削除。"""
        existing = [
            post("gone", "hajimemasite", "2026-06-03", "2026-06-03T10:00:00Z"),
            post("stay-a", "力", "2026-06-05", "2026-06-05T15:00:00Z"),
            post("stay-b", "deepen", "2026-06-05", "2026-06-05T04:00:00Z"),
        ]
        fresh = [
            post("stay-a", "力", "2026-06-05", "2026-06-05T15:00:00Z"),
            post("stay-b", "deepen", "2026-06-05", "2026-06-05T04:00:00Z"),
        ]
        window = [
            ("stay-a", "2026-06-05T15:00:00Z"),
            ("stay-b", "2026-06-05T04:00:00Z"),
        ]
        merged = merge_diary_posts(existing, fresh, window, limit_reached=False)
        self.assertEqual(
            [p["instagramMediaId"] for p in merged],
            ["stay-a", "stay-b"],
        )

    def test_keeps_existing_when_video_skipped_in_window(self) -> None:
        existing = [
            post("video", "was-synced", "2026-06-05", "2026-06-05T18:00:00Z"),
        ]
        fresh: list[dict] = []
        window = [
            ("video", "2026-06-05T18:00:00Z"),
            ("img", "2026-06-05T12:00:00Z"),
        ]
        merged = merge_diary_posts(existing, fresh, window, limit_reached=False)
        self.assertEqual([p["instagramMediaId"] for p in merged], ["video"])


class VerifyMergedPostsTests(unittest.TestCase):
    def test_verify_passes_after_successful_delete(self) -> None:
        existing = [
            post("gone", "deleted", "2026-06-03", "2026-06-03T10:00:00Z"),
            post("stay", "latest", "2026-06-05", "2026-06-05T12:00:00Z"),
        ]
        fresh = [post("stay", "latest", "2026-06-05", "2026-06-05T12:00:00Z")]
        window = [("stay", "2026-06-05T12:00:00Z")]
        merged = merge_diary_posts(existing, fresh, window, limit_reached=False)
        self.assertEqual(verify_merged_posts(existing, merged, window, False), [])

    def test_verify_detects_stale_post_left_behind(self) -> None:
        existing = [
            post("gone", "deleted", "2026-06-03", "2026-06-03T10:00:00Z"),
            post("stay", "latest", "2026-06-05", "2026-06-05T12:00:00Z"),
        ]
        window = [("stay", "2026-06-05T12:00:00Z")]
        bad_merged = existing[:]
        errors = verify_merged_posts(existing, bad_merged, window, limit_reached=False)
        self.assertTrue(errors)
        self.assertEqual(len(find_undeleted_posts(existing, bad_merged, window, False)), 1)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
