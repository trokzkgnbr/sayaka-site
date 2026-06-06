#!/usr/bin/env bash
# instagram.env の値を GitHub Actions Secrets に登録する（1回だけ）
# 使い方:
#   1. https://github.com/settings/tokens → Fine-grained または classic
#      権限: sayaka-site の Secrets 書き込み（classic なら repo）
#   2. ターミナルで（トークンはチャットに貼らない）:
#        export GH_TOKEN='ghp_...'
#        bash scripts/setup_github_secrets.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/config/instagram.env"
REPO="${GITHUB_REPO:-trokzkgnbr/sayaka-site}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "× $ENV_FILE がありません。先に bash scripts/setup_instagram_env.sh" >&2
  exit 1
fi

TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
if [[ -z "$TOKEN" ]]; then
  echo "× GH_TOKEN または GITHUB_TOKEN を export してから再実行してください。" >&2
  echo "  例: export GH_TOKEN='ghp_xxxxxxxx'" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

for key in INSTAGRAM_ACCESS_TOKEN INSTAGRAM_USER_ID INSTAGRAM_APP_ID INSTAGRAM_APP_SECRET; do
  if [[ -z "${!key:-}" ]]; then
    echo "× instagram.env の $key が空です" >&2
    exit 1
  fi
done

if [[ -z "${INSTAGRAM_USER_ACCESS_TOKEN:-}" ]]; then
  echo "INSTAGRAM_USER_ACCESS_TOKEN を ACCESS_TOKEN から取得します..."
  python3 "$ROOT/scripts/ensure_instagram_user_access_token.py"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

if [[ -z "${INSTAGRAM_USER_ACCESS_TOKEN:-}" ]]; then
  echo "× INSTAGRAM_USER_ACCESS_TOKEN を取得できませんでした" >&2
  exit 1
fi

if ! python3 -c "import nacl" 2>/dev/null; then
  python3 -m pip install --user PyNaCl
fi

export GITHUB_REPO="$REPO"
export GH_TOKEN="$TOKEN"

python3 << 'PY'
import base64
import json
import os
import urllib.error
import urllib.request
from nacl import encoding, public

repo = os.environ["GITHUB_REPO"]
gh = os.environ["GH_TOKEN"]
secrets = {
    "INSTAGRAM_ACCESS_TOKEN": os.environ["INSTAGRAM_ACCESS_TOKEN"],
    "INSTAGRAM_USER_ACCESS_TOKEN": os.environ["INSTAGRAM_USER_ACCESS_TOKEN"],
    "INSTAGRAM_USER_ID": os.environ["INSTAGRAM_USER_ID"],
    "INSTAGRAM_APP_ID": os.environ["INSTAGRAM_APP_ID"],
    "INSTAGRAM_APP_SECRET": os.environ["INSTAGRAM_APP_SECRET"],
}

def api(method, url, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {gh}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)

def encrypt(pub_b64: str, value: str) -> str:
    pub = public.PublicKey(pub_b64.encode(), encoding.Base64Encoder())
    sealed = public.SealedBox(pub)
    return base64.b64encode(sealed.encrypt(value.encode())).decode()

pk = api("GET", f"https://api.github.com/repos/{repo}/actions/secrets/public-key")
for name, value in secrets.items():
    body = {
        "encrypted_value": encrypt(pk["key"], value),
        "key_id": pk["key_id"],
    }
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
        data=json.dumps(body).encode(),
        method="PUT",
        headers={
            "Authorization": f"Bearer {gh}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"× {name}: HTTP {e.code} {e.read().decode()[:200]}")
    print(f"OK: {name}")
print(f"\n完了: https://github.com/{repo}/settings/secrets/actions")
PY
