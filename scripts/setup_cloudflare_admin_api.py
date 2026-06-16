#!/usr/bin/env python3
"""Cloudflare Worker 用の wrangler secret 設定手順を表示。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def read_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        out[k.strip()] = v.strip()
    return out


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    env = read_env(root / "config" / "admin.env")
    pwd_hash = env.get("ADMIN_PASSWORD_HASH", "")
    session = env.get("SESSION_SECRET", "")
    github = env.get("GITHUB_TOKEN", "")

    print("Cloudflare Worker に Blog 管理 API を載せます（Mac 不要）。")
    print()
    if not pwd_hash or not session:
        print("× config/admin.env に ADMIN_PASSWORD_HASH / SESSION_SECRET がありません")
        return 1

    cmds = [
        ("ADMIN_PASSWORD_HASH", pwd_hash),
        ("SESSION_SECRET", session),
    ]
    if github:
        cmds.append(("GITHUB_TOKEN", github))
    else:
        print("警告: GITHUB_TOKEN 未設定 — Worker から GitHub へ push できません")
        print("  config/admin.env に repo 権限付き PAT を追加してください")
        print()

    print("wrangler login 後、次を実行:")
    print()
    for name, value in cmds:
        print(f'printf %s "{value}" | wrangler secret put {name}')
    print()
    print("デプロイ:")
    print("  npx wrangler deploy")
    print()
    print("DNS が Cloudflare 経由である必要があります。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
