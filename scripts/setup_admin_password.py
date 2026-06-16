#!/usr/bin/env python3
"""管理パスワードのハッシュと SESSION_SECRET を config/admin.env に書く。"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import secrets
import sys
from pathlib import Path


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 600_000
    )
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--password-stdin", action="store_true")
    args = parser.parse_args()

    if args.password_stdin:
        password = sys.stdin.read().strip()
    else:
        password = getpass.getpass("Blog 管理用パスワード: ")
        confirm = getpass.getpass("もう一度: ")
        if password != confirm:
            print("× 一致しません", file=sys.stderr)
            return 1

    if len(password) < 8:
        print("× 8文字以上にしてください", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[1]
    example = root / "config" / "admin.env.example"
    target = root / "config" / "admin.env"

    lines = example.read_text(encoding="utf-8").splitlines(keepends=True)
    pwd_hash = hash_password(password)
    session_secret = secrets.token_hex(32)

    out: list[str] = []
    for line in lines:
        if line.startswith("ADMIN_PASSWORD_HASH="):
            out.append(f"ADMIN_PASSWORD_HASH={pwd_hash}\n")
        elif line.startswith("SESSION_SECRET="):
            out.append(f"SESSION_SECRET={session_secret}\n")
        else:
            out.append(line)

    target.write_text("".join(out), encoding="utf-8")
    try:
        target.chmod(0o600)
    except OSError:
        pass

    print(f"保存: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
