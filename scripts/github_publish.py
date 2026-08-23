"""Blog データを GitHub リポジトリへ push する（外出先管理サーバー用）。"""

from __future__ import annotations

import base64
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class GitHubPublishError(Exception):
    pass


def _request(
    url: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any] | None:
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "sayaka-portfolio-diary-admin",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubPublishError(f"GitHub API {exc.code}: {body}") from exc


def github_settings(env: dict[str, str]) -> tuple[str, str, str]:
    token = env.get("GITHUB_TOKEN", "").strip()
    repo = env.get("GITHUB_REPO", "trokzkgnbr/sayaka-site").strip()
    branch = env.get("GITHUB_BRANCH", "main").strip() or "main"
    if not token:
        raise GitHubPublishError("GITHUB_TOKEN が未設定です")
    if not repo or "/" not in repo:
        raise GitHubPublishError("GITHUB_REPO が不正です")
    return token, repo, branch


def get_file_meta(path: str, env: dict[str, str]) -> dict[str, Any] | None:
    token, repo, branch = github_settings(env)
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={urllib.parse.quote(branch)}"
    try:
        result = _request(url, token)
    except GitHubPublishError as exc:
        if "404" in str(exc):
            return None
        raise
    if not isinstance(result, dict):
        return None
    return result


def get_file_bytes(path: str, env: dict[str, str]) -> bytes | None:
    meta = get_file_meta(path, env)
    if not meta:
        return None
    content = meta.get("content")
    if not isinstance(content, str):
        return None
    return base64.b64decode(content)


def load_diary_from_github(env: dict[str, str]) -> dict[str, Any]:
    raw = get_file_bytes("data/diary.json", env)
    if raw is None:
        return {"posts": []}
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        return {"posts": []}
    posts = data.get("posts")
    if not isinstance(posts, list):
        posts = []
    return {"posts": posts}


def _put_file(
    repo_path: str,
    content: bytes,
    message: str,
    env: dict[str, str],
    *,
    sha: str | None = None,
) -> None:
    token, repo, branch = github_settings(env)
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
    payload: dict[str, Any] = {
        "message": message,
        "content": base64.b64encode(content).decode("ascii"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    _request(url, token, method="PUT", payload=payload)


def _delete_file(repo_path: str, message: str, env: dict[str, str], sha: str) -> None:
    token, repo, branch = github_settings(env)
    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
    payload = {"message": message, "sha": sha, "branch": branch}
    _request(url, token, method="DELETE", payload=payload)


def publish_diary_changes(
    env: dict[str, str],
    diary_data: dict[str, Any],
    *,
    message: str,
    new_images: dict[str, bytes] | None = None,
    deleted_images: list[str] | None = None,
) -> None:
    new_images = new_images or {}
    deleted_images = deleted_images or []

    for rel_path, blob in new_images.items():
        repo_path = rel_path.lstrip("/")
        meta = get_file_meta(repo_path, env)
        _put_file(repo_path, blob, message, env, sha=meta.get("sha") if meta else None)

    diary_json = json.dumps(diary_data, ensure_ascii=False, indent=2) + "\n"
    diary_meta = get_file_meta("data/diary.json", env)
    _put_file(
        "data/diary.json",
        diary_json.encode("utf-8"),
        message,
        env,
        sha=diary_meta.get("sha") if diary_meta else None,
    )

    for rel_path in deleted_images:
        repo_path = rel_path.lstrip("/")
        meta = get_file_meta(repo_path, env)
        if meta and meta.get("sha"):
            _delete_file(repo_path, message, env, str(meta["sha"]))


def github_enabled(env: dict[str, str]) -> bool:
    return bool(env.get("GITHUB_TOKEN", "").strip())


def check_github(env: dict[str, str]) -> tuple[bool, str | None]:
    try:
        token, repo, _branch = github_settings(env)
    except GitHubPublishError as exc:
        return False, str(exc)
    url = f"https://api.github.com/repos/{repo}"
    try:
        _request(url, token)
        return True, None
    except GitHubPublishError as exc:
        text = str(exc)
        if "401" in text or "403" in text:
            return (
                False,
                "GitHub 連携の期限が切れているか、権限がありません。寺尾までご連絡ください。",
            )
        return False, text
