#!/usr/bin/env python3
"""GitHub Actions: 直近で同期済みなら schedule 実行をスキップする。"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

SKIP_WITHIN = timedelta(minutes=90)
DIARY_PATH = Path(__file__).resolve().parent.parent / "data" / "diary.json"


def write_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT", "").strip()
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def parse_synced_at(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def main() -> int:
    event = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    if event == "workflow_dispatch":
        print("手動実行のためスキップしません。")
        write_output("skip", "false")
        return 0

    if not DIARY_PATH.is_file():
        print("diary.json が無いため同期を実行します。")
        write_output("skip", "false")
        return 0

    data = json.loads(DIARY_PATH.read_text(encoding="utf-8"))
    synced_at = parse_synced_at(str(data.get("lastSyncedAt", "")))
    if synced_at is None:
        print("lastSyncedAt が無いため同期を実行します。")
        write_output("skip", "false")
        return 0

    age = datetime.now(timezone.utc) - synced_at.astimezone(timezone.utc)
    if age < SKIP_WITHIN:
        print(
            f"直近 {int(age.total_seconds() // 60)} 分前に同期済みのためスキップします "
            f"(lastSyncedAt={synced_at.isoformat()})。"
        )
        write_output("skip", "true")
        return 0

    print(
        f"前回同期から {int(age.total_seconds() // 60)} 分経過。同期を実行します "
        f"(lastSyncedAt={synced_at.isoformat()})。"
    )
    write_output("skip", "false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
