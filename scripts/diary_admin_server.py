#!/usr/bin/env python3
"""
Blog 管理サーバー。

- パスワードは ADMIN_PASSWORD_HASH（平文は Git に入れない）
- 既定は 127.0.0.1（ローカル）。外出先利用時は ADMIN_PATH + GITHUB_TOKEN でクラウド公開
- admin/ は GitHub Pages には載せない
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
from urllib.parse import urlparse

JST = timezone(timedelta(hours=9))
SESSION_COOKIE = "diary_admin_session"
SESSION_TTL = 60 * 60 * 12  # 12h
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def site_root() -> Path:
    return Path(__file__).resolve().parents[1]


sys.path.insert(0, str(Path(__file__).resolve().parent))


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    for key, value in os.environ.items():
        if not value.strip():
            continue
        if key in {
            "ADMIN_PASSWORD_HASH",
            "SESSION_SECRET",
            "ADMIN_BIND",
            "ADMIN_PORT",
            "ADMIN_PATH",
            "ADMIN_HTTPS",
            "GITHUB_TOKEN",
            "GITHUB_REPO",
            "GITHUB_BRANCH",
            "PORT",
        }:
            env[key] = value.strip()
    if os.environ.get("PORT") and not env.get("ADMIN_PORT"):
        env["ADMIN_PORT"] = os.environ["PORT"].strip()
    return env


def normalize_admin_path(raw: str) -> str:
    value = raw.strip().strip("/")
    if not value or ".." in value or "/" in value or not re.fullmatch(r"[a-zA-Z0-9_-]+", value):
        raise ValueError("ADMIN_PATH は英数字・-_ のみ（例: blog-mgt-k7p2xq9）")
    return f"/{value}"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 600_000
    )
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def write_admin_env(env_path: Path, password: str) -> dict[str, str]:
    example = env_path.parent / "admin.env.example"
    if not example.is_file():
        raise FileNotFoundError("config/admin.env.example がありません")
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
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text("".join(out), encoding="utf-8")
    try:
        env_path.chmod(0o600)
    except OSError:
        pass
    return load_env(env_path)


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


def load_diary_local() -> dict[str, Any]:
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


def save_diary_local(data: dict[str, Any]) -> None:
    path = diary_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_diary(env: dict[str, str]) -> dict[str, Any]:
    from github_publish import github_enabled, load_diary_from_github

    if github_enabled(env):
        try:
            return load_diary_from_github(env)
        except Exception as exc:
            sys.stderr.write(f"GitHub から diary を読めませんでした: {exc}\n")
    return load_diary_local()


def persist_diary(
    env: dict[str, str],
    data: dict[str, Any],
    *,
    message: str,
    new_images: dict[str, bytes] | None = None,
    deleted_images: list[str] | None = None,
) -> None:
    from github_publish import GitHubPublishError, github_enabled, publish_diary_changes

    save_diary_local(data)
    if github_enabled(env):
        try:
            publish_diary_changes(
                env,
                data,
                message=message,
                new_images=new_images,
                deleted_images=deleted_images,
            )
        except GitHubPublishError as exc:
            raise RuntimeError(str(exc)) from exc


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
    env_path: Path = site_root() / "config" / "admin.env"
    admin_dir: Path = site_root() / "admin"
    admin_prefix: str = "/admin"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    @classmethod
    def setup_required(cls) -> bool:
        return not cls.env.get("ADMIN_PASSWORD_HASH") or not cls.env.get("SESSION_SECRET")

    def _admin_url(self, suffix: str = "") -> str:
        suffix = suffix.lstrip("/")
        if not suffix:
            return f"{self.admin_prefix}/"
        return f"{self.admin_prefix}/{suffix}"

    def _cookie_header(self, value: str, *, max_age: int | None = None) -> str:
        secure = (
            self.env.get("ADMIN_HTTPS") == "1"
            or self.headers.get("X-Forwarded-Proto", "").lower() == "https"
        )
        parts = [
            f"{SESSION_COOKIE}={value}",
            f"Path={self.admin_prefix}/",
            "HttpOnly",
            "SameSite=Strict",
        ]
        if secure:
            parts.append("Secure")
        if max_age is not None:
            parts.append(f"Max-Age={max_age}")
        return "; ".join(parts)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def _json_response(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str, cookie: str | None = None, clear_cookie: bool = False) -> None:
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        if cookie:
            self.send_header("Set-Cookie", self._cookie_header(cookie, max_age=SESSION_TTL))
        if clear_cookie:
            self.send_header("Set-Cookie", self._cookie_header("", max_age=0))
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
        if self.setup_required():
            if name not in {"setup.html", "login.html"}:
                self._redirect(self._admin_url("setup.html"))
                return
            if name == "login.html":
                self._redirect(self._admin_url("setup.html"))
                return
        elif name == "setup.html":
            self._redirect(self._admin_url("login.html"))
            return

        protected = {"index.html", "register.html", "delete.html"}
        if name in protected and not self._authenticated():
            if self.setup_required():
                self._redirect(self._admin_url("setup.html"))
            else:
                self._redirect(self._admin_url("login.html"))
            return
        path = self.admin_dir / name
        if not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self._serve_file(path)

    def _serve_admin_static(self, rel: str) -> None:
        if ".." in rel or rel.startswith("/"):
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        path = self.admin_dir / rel
        self._serve_file(path)

    def _path_under_admin(self, path: str) -> str | None:
        prefix = self.admin_prefix
        if path == prefix or path == prefix + "/":
            return ""
        needle = prefix + "/"
        if path.startswith(needle):
            return path[len(needle) :]
        return None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        admin_rel = self._path_under_admin(path)

        if admin_rel is not None:
            if admin_rel == "api/posts":
                if not self._require_auth_api():
                    return
                data = load_diary(self.env)
                posts = sorted(
                    data.get("posts", []),
                    key=lambda p: p.get("publishedAt") or p.get("date") or "",
                    reverse=True,
                )
                self._json_response(HTTPStatus.OK, {"ok": True, "posts": posts})
                return

            if admin_rel == "api/session":
                self._json_response(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "authenticated": self._authenticated(),
                        "setupRequired": self.setup_required(),
                    },
                )
                return

            if admin_rel == "" or admin_rel == "index.html":
                self._serve_admin_page("index.html")
                return

            if admin_rel.endswith("/"):
                admin_rel += "index.html"

            if admin_rel.endswith(".html"):
                self._serve_admin_page(admin_rel)
                return

            self._serve_admin_static(admin_rel)
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
            if file_path.is_file():
                self._serve_file(file_path)
                return
            from github_publish import get_file_bytes, github_enabled

            if github_enabled(self.env):
                blob = get_file_bytes(rel, self.env)
                if blob:
                    ctype = mimetypes.guess_type(rel)[0] or "application/octet-stream"
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(blob)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(blob)
                    return
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if path.startswith("/images/"):
            rel = path.lstrip("/")
            if ".." in rel:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            self._serve_file(site_root() / rel)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        admin_rel = self._path_under_admin(path)
        if admin_rel is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        if admin_rel == "api/setup":
            if not self.setup_required():
                self._json_response(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "すでにパスワードが設定されています"},
                )
                return
            try:
                payload = json.loads(self._read_body().decode("utf-8"))
            except json.JSONDecodeError:
                self._json_response(HTTPStatus.BAD_REQUEST, {"ok": False, "error": "JSON が不正です"})
                return
            password = str(payload.get("password", ""))
            confirm = str(payload.get("confirm", ""))
            if len(password) < 8:
                self._json_response(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "パスワードは8文字以上にしてください"},
                )
                return
            if password != confirm:
                self._json_response(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "パスワードが一致しません"},
                )
                return
            try:
                self.__class__.env = write_admin_env(self.env_path, password)
            except FileNotFoundError as exc:
                self._json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})
                return
            self._json_response(HTTPStatus.OK, {"ok": True})
            return

        if admin_rel == "api/login":
            if self.setup_required():
                self._json_response(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "先に初回セットアップでパスワードを設定してください"},
                )
                return
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
            self.send_header("Set-Cookie", self._cookie_header(token, max_age=SESSION_TTL))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if admin_rel == "api/logout":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", self._cookie_header("", max_age=0))
            self.send_header("Content-Length", "11")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return

        if admin_rel == "api/posts":
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

            image_bytes = file_item.file.read()
            post_id = f"post-{uuid.uuid4().hex[:12]}"
            fname = safe_image_name(post_id)
            rel_image = f"images/diary/{fname}"
            dest = images_dir() / fname
            images_dir().mkdir(parents=True, exist_ok=True)
            dest.write_bytes(image_bytes)

            post = {
                "id": post_id,
                "date": date_str,
                "publishedAt": published_at_from_date(date_str),
                "title": title_from_body(body_text),
                "body": body_text,
                "image": rel_image,
            }

            data = load_diary(self.env)
            posts = data.setdefault("posts", [])
            posts.insert(0, post)
            try:
                persist_diary(
                    self.env,
                    data,
                    message="Update blog posts.",
                    new_images={rel_image: image_bytes},
                )
            except RuntimeError as exc:
                self._json_response(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
                return
            self._json_response(HTTPStatus.OK, {"ok": True, "post": post, "published": True})
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        admin_rel = self._path_under_admin(parsed.path)
        if admin_rel is None or not admin_rel.startswith("api/posts/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self._require_auth_api():
            return

        post_id = admin_rel.rsplit("/", 1)[-1]
        data = load_diary(self.env)
        posts = data.get("posts", [])
        target = next((p for p in posts if p.get("id") == post_id), None)
        if not target:
            self._json_response(HTTPStatus.NOT_FOUND, {"ok": False, "error": "投稿が見つかりません"})
            return

        data["posts"] = [p for p in posts if p.get("id") != post_id]
        deleted_image = str(target.get("image") or "")
        img_path = site_root() / deleted_image if deleted_image else None
        if img_path and img_path.is_file():
            img_path.unlink()

        try:
            persist_diary(
                self.env,
                data,
                message="Update blog posts.",
                deleted_images=[deleted_image] if deleted_image else None,
            )
        except RuntimeError as exc:
            self._json_response(HTTPStatus.BAD_GATEWAY, {"ok": False, "error": str(exc)})
            return

        self._json_response(HTTPStatus.OK, {"ok": True, "deleted": post_id, "published": True})


def public_base_url(env: dict[str, str], bind: str, port: int, admin_prefix: str) -> str:
    public = env.get("ADMIN_PUBLIC_URL", "").strip().rstrip("/")
    if public:
        return f"{public}{admin_prefix}/"
    host = bind if bind not in {"0.0.0.0", "::"} else "127.0.0.1"
    return f"http://{host}:{port}{admin_prefix}/"


def main() -> int:
    root = site_root()
    env_path = root / "config" / "admin.env"
    example = root / "config" / "admin.env.example"

    if not env_path.is_file() and example.is_file():
        env_path.parent.mkdir(parents=True, exist_ok=True)
        env_path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            env_path.chmod(0o600)
        except OSError:
            pass
        print(f"初回: {env_path} を作成しました")
    elif not env_path.is_file() and not example.is_file():
        print("× config/admin.env.example がありません", file=sys.stderr)
        return 1

    env = load_env(env_path)
    try:
        admin_prefix = normalize_admin_path(env.get("ADMIN_PATH", "admin"))
    except ValueError as exc:
        print(f"× {exc}", file=sys.stderr)
        return 1

    bind = env.get("ADMIN_BIND", "127.0.0.1")
    port = int(env.get("ADMIN_PORT", "8765"))

    DiaryAdminHandler.env = env
    DiaryAdminHandler.env_path = env_path
    DiaryAdminHandler.admin_dir = root / "admin"
    DiaryAdminHandler.admin_prefix = admin_prefix

    server = ThreadingHTTPServer((bind, port), DiaryAdminHandler)
    base = public_base_url(env, bind, port, admin_prefix)
    if DiaryAdminHandler.setup_required():
        url = f"{base}setup.html"
        print(f"Blog 管理サーバー（初回セットアップ）: {url}")
        print("ブラウザでパスワードを設定してください")
    else:
        print(f"Blog 管理サーバー: {base}")
    if env.get("GITHUB_TOKEN"):
        print("GitHub 自動反映: 有効（投稿・削除後に main へ push）")
    print("停止: Ctrl+C")
    if bind == "127.0.0.1":
        print("（127.0.0.1 のみ。外出先公開は Render 等 + ADMIN_BIND=0.0.0.0 を参照）")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
