#!/usr/bin/env python3
"""GitHub Actions Secret を1件登録する（GH_TOKEN 必須）。"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

from nacl import encoding, public


def api(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def encrypt(pub_b64: str, value: str) -> str:
    pub = public.PublicKey(pub_b64.encode(), encoding.Base64Encoder())
    sealed = public.SealedBox(pub)
    return base64.b64encode(sealed.encrypt(value.encode())).decode()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--value", required=True)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPO", "trokzkgnbr/sayaka-site"))
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("× GH_TOKEN または GITHUB_TOKEN を export してください。", file=sys.stderr)
        return 1

    pk = api("GET", f"https://api.github.com/repos/{args.repo}/actions/secrets/public-key", token)
    body = {
        "encrypted_value": encrypt(pk["key"], args.value),
        "key_id": pk["key_id"],
    }
    req = urllib.request.Request(
        f"https://api.github.com/repos/{args.repo}/actions/secrets/{args.name}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as exc:
        print(f"× HTTP {exc.code}: {exc.read().decode()[:300]}", file=sys.stderr)
        return 1

    print(f"OK: {args.name} → https://github.com/{args.repo}/settings/secrets/actions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
