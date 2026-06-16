#!/usr/bin/env python3
"""
Blog 管理用ローカルサーバー。

- パスワードは config/admin.env のハッシュのみ（平文は Git に入れない）
- 既定は 127.0.0.1 のみ（インターネットから直接アクセス不可）
- admin/ は GitHub Pages には公開されない
"""

from __future__ import annotations

import base64
import cgi
import hashlib
import hmac
import io
import json
import mimetypes
import os
import re
import secrets
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

JST = timezone(timedelta(hours=9))
SESSION_COOKIE = "diary_admin_session"
SESSION_TTL = 60 * 60 * 12  # 12h
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def site_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt, digest_hex = stored.split("$", 2)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 600_000
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def sign_session(secret: str, payload: str) -> str:
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    raw = f"{payload}.{base64.urlsafe_b64encode(sig).decode().rstrip('=')}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def verify_session(secret: str, token: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(token + "==").decode()
        payload, sig_b64 = raw.rsplit(".", 1)
        expected = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).digest()
        given = base64.urlsafe_b64decode(sig_b64 + "==")
        if not hmac.compare_digest(expected, given):
            return False
        user, exp_str = payload.split("|", 1)
        if user != "admin":
            return False
        return int(exp_str) > int(time.time())
    except (ValueError, OSError):
        return False


def make_session(secret: str) -> str:
    exp = int(time.time()) + SESSION_TTL
    return sign_session(secret, f"admin|{exp}")


def diary_path() -> Path:
    return site_root() / "data" / "diary.json"


def images_dir() -> Path:
    return site_root() / "images" / "diary"


def load_diary() -> dict[str, Any]:
    path = diary_path()
    if not path.is_file():
        return {"posts": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"posts": []}
    posts = data.get("posts")
    if not isinstance(posts, list):
        posts = []
    return {"posts": posts}


def save_diary(data: dict[str, Any]) -> None:
    path = diary_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def title_from_body(body: str) -> str:
    text = body.strip()
    if not text:
        return "（無題）"
    return text.splitlines()[0].strip() or "（無題）"


def normalize_date(raw: str) -> str:
    value = raw.strip()
    if not value:
        return datetime.now(JST).strftime("%Y-%m-%d")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("日付は YYYY-MM-DD 形式で入力してください")
    return value


def published_at_from_date(date_str: str) -> str:
    now = datetime.now(timezone.utc)
    return f"{date_str}T{now.strftime('%H:%M:%S')}Z"


def safe_image_name(post_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "", post_id)
    return f"{safe}.jpg"


class DiaryAdminHandler(BaseHTTPRequestHandler):
    env: dict[str, str] = {}
    admin_dir: Path = site_root() / "admin"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def _json_response(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str, cookie: str | None = None, clear_cookie: bool = False) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        if cookie:
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE}={cookie}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}",
            )
        if clear_cookie:
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0",
            )
        self.end_headers()

    def _session_token(self) -> str | None:
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith(f"{SESSION_COOKIE}="):
                return part.split("=", 1)[1]
        return None

    def _authenticated(self) -> bool:
        secret = self.env.get("SESSION_SECRET", "")
        token = self._session_token()
        if not secret or not token:
            return False
        return verify_session(secret, token)

    def _require_auth_api(self) -> bool:
        if self._authenticated():
            return True
        self._json_response(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "ログインが必要です"})
        return False

    def _serve_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        header = f"{ctype}; charset=utf-8" if ctype.startswith("text/") else ctype
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", header)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _serve_admin_page(self, name: str) -> None:
        protected = {"index.html", "register.html", "delete.html"}
        if name in protected and not self._authenticated():
            self._redirect("/admin/login.html")
            return
        path = self.admin_dir / name
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/admin/api/posts":
            if not self._require_auth_api():
                return
            data = load_diary()
            posts = sorted(
                data.get("posts", []),
                key=lambda p: p.get("publishedAt") or p.get("date") or "",
                reverse=True,
            )
            self._json_response(HTTPStatus.OK, {"ok": True, "posts": posts})
            return

        if path == "/admin/api/session":
            self._json_response(
                HTTPStatus.OK,
                {"ok": True, "authenticated": self._authenticated()},
            )
            return

        if path.startswith("/images/diary/"):
            if not self._authenticated():
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            rel = path.lstrip("/")
            if ".." in rel:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            file_path = site_root() / rel
            self._serve_file(file_path)
            return

        if path == "/admin" or path == "/admin/":
            self._serve_admin_page("index.html")
            return

        if path.startswith("/admin/"):
            rel = path[len("/admin/") :]
            if ".." in rel or rel.startswith("/"):
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if rel.endswith("/"):
                rel += "index.html"
            self._serve_admin_page(rel)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/admin/api/login":
            try:
                payload = json.loads(self._read_body().decode("utf-8"))
            except json.JSONDecodeError:
                self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "JSON が不正です"})
                return
            password = str(payload.get("password", ""))
            stored = self.env.get("ADMIN_PASSWORD_HASH", "")
            secret = self.env.get("SESSION_SECRET", "")
            if not stored or not secret or not verify_password(password, stored):
                time.sleep(0.8)
                self._json_response(HTTPStatus.UNAUTHORIZED, {"ok": False, "error": "パスワードが違います"})
                return
            token = make_session(secret)
            body = json.dumps({"ok": True}, ensure_ascii=False).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_TTL}",
            )
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/admin/api/logout":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0",
            )
            self.send_header("Content-Length", "11")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return

        if path == "/admin/api/posts":
            if not self._require_auth_api():
                return
            ctype = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in ctype:
                self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "multipart が必要です"})
                return
            body = self._read_body()
            environ = {
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": ctype,
                "CONTENT_LENGTH": str(len(body)),
            }
            form = cgi.FieldStorage(fp=io.BytesIO(body), environ=environ, keep_blank_values=True)

            body_text = form.getfirst("body", "").strip()
            if not body_text:
                self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "本文を入力してください"})
                return

            try:
                date_str = normalize_date(form.getfirst("date", "") or "")
            except ValueError as exc:
                self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
                return

            file_item = form["image"] if "image" in form else None
            if file_item is None or not getattr(file_item, "file", None) or not file_item.filename:
                self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "画像を選んでください"})
                return

            mime = file_item.type or mimetypes.guess_type(file_item.filename)[0] or ""
            if mime not in ALLOWED_IMAGE_TYPES:
                self._json_response(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "画像は JPEG / PNG / WebP にしてください"},
                )
                return

            post_id = f"post-{uuid.uuid4().hex[:12]}"
            fname = safe_image_name(post_id)
            rel_image = f"images/diary/{fname}"
            dest = images_dir() / fname
            images_dir().mkdir(parents=True, exist_ok=True)
            dest.write_bytes(file_item.file.read())

            post = {
                "id": post_id,
                "date": date_str,
                "publishedAt": published_at_from_date(date_str),
                "title": title_from_body(body_text),
                "body": body_text,
                "image": rel_image,
            }

            data = load_diary()
            posts = data.setdefault("posts", [])
            posts.insert(0, post)
            save_diary(data)
            self._json_response(HTTPStatus.OK, {"ok": True, "post": post})
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/admin/api/posts/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self._require_auth_api():
            return

        post_id = parsed.path.rsplit("/", 1)[-1]
        data = load_diary()
        posts = data.get("posts", [])
        target = next((p for p in posts if p.get("id") == post_id), None)
        if not target:
            self._json_response(HTTPStatus.NOT_FOUND, {"ok": False, "error": "投稿が見つかりません"})
            return

        data["posts"] = [p for p in posts if p.get("id") != post_id]
        save_diary(data)

        image = target.get("image")
        if image:
            img_path = site_root() / str(image)
            if img_path.is_file():
                img_path.unlink()

        self._json_response(HTTPStatus.OK, {"ok": True, "deleted": post_id})


def main() -> int:
    root = site_root()
    env_path = root / "config" / "admin.env"
    env = load_env(env_path)

    if not env.get("ADMIN_PASSWORD_HASH") or not env.get("SESSION_SECRET"):
        print("× config/admin.env の ADMIN_PASSWORD_HASH / SESSION_SECRET を設定してください", file=sys.stderr)
        print("  bash scripts/setup_admin_password.sh", file=sys.stderr)
        return 1

    bind = env.get("ADMIN_BIND", "127.0.0.1")
    port = int(env.get("ADMIN_PORT", "8765"))

    DiaryAdminHandler.env = env
    DiaryAdminHandler.admin_dir = root / "admin"

    server = ThreadingHTTPServer((bind, port), DiaryAdminHandler)
    url = f"http://{bind}:{port}/admin/"
    print(f"Blog 管理サーバー: {url}")
    print("停止: Ctrl+C")
    if bind == "127.0.0.1":
        print("（127.0.0.1 のみ。インターネットから直接はアクセスできません）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
