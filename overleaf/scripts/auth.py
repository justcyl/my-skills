#!/usr/bin/env python3
"""Authenticate to a self-hosted Overleaf instance using an existing account.

The password is read from a protected file or command and never printed. A
short-lived cookie cache avoids logging in on every CLI invocation.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


def _host() -> str:
    host = os.environ.get("OVERLEAF_HOST", "www.overleaf.com")
    host = host.removeprefix("https://").removeprefix("http://").rstrip("/")
    return host


def _base_url() -> str:
    scheme = os.environ.get("OVERLEAF_SCHEME", "https").rstrip(":")
    return f"{scheme}://{_host()}"


def _cache_path() -> pathlib.Path:
    root = pathlib.Path(
        os.environ.get("XDG_CACHE_HOME", pathlib.Path.home() / ".cache")
    )
    return root / "overleaf" / "session.json"


def _cookie_header(session: requests.Session) -> str:
    values: dict[str, str] = {}
    for cookie in session.cookies:
        values[cookie.name] = cookie.value
    return "; ".join(f"{name}={value}" for name, value in values.items())


def _valid_cached_session() -> str | None:
    path = _cache_path()
    try:
        payload = json.loads(path.read_text())
        cookie = str(payload["cookie"])
        expires_at = float(payload.get("expires_at", 0))
        if expires_at <= time.time() + 300:
            return None
    except (OSError, ValueError, KeyError, TypeError):
        return None

    try:
        response = requests.get(
            urljoin(_base_url() + "/", "user/projects"),
            headers={"Accept": "application/json", "Cookie": cookie},
            allow_redirects=True,
            timeout=16,
        )
        final_path = response.url.split("?", 1)[0].rstrip("/")
        content_type = response.headers.get("Content-Type", "").lower()
        if response.ok and "json" in content_type and not final_path.endswith("/login"):
            return cookie
    except requests.RequestException:
        pass
    return None


def _read_password() -> str:
    password_file = os.environ.get(
        "OVERLEAF_PASSWORD_FILE",
        str(pathlib.Path.home() / ".config/overleaf/password"),
    )
    if os.environ.get("OVERLEAF_PASSWORD_COMMAND"):
        result = subprocess.run(
            os.environ["OVERLEAF_PASSWORD_COMMAND"],
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    try:
        return pathlib.Path(password_file).read_text().strip()
    except OSError as exc:
        raise RuntimeError(f"无法读取密码文件：{password_file}") from exc


def _login() -> str:
    email = os.environ.get("OVERLEAF_EMAIL", "").strip()
    if not email:
        raise RuntimeError("未设置 OVERLEAF_EMAIL。")
    password = _read_password()
    if not password:
        raise RuntimeError("密码为空。")

    base = _base_url()
    session = requests.Session()
    login_page = session.get(f"{base}/login", timeout=16)
    login_page.raise_for_status()
    soup = BeautifulSoup(login_page.text, "html.parser")
    csrf_node = soup.select_one('input[name="_csrf"]')
    if csrf_node is None or not csrf_node.get("value"):
        csrf_node = soup.select_one('meta[name="ol-csrfToken"]')
    csrf = (csrf_node.get("value") or csrf_node.get("content")) if csrf_node else None
    if not csrf:
        raise RuntimeError("登录页没有找到 CSRF token。")

    response = session.post(
        f"{base}/login",
        data={"_csrf": csrf, "email": email, "password": password},
        allow_redirects=True,
        timeout=16,
    )
    response.raise_for_status()
    final_path = response.url.split("?", 1)[0].rstrip("/")
    cookie = _cookie_header(session)
    if not cookie or final_path.endswith("/login") or "overleaf.sid=" not in cookie:
        raise RuntimeError("登录失败：账号或密码不正确，或登录流程发生变化。")

    cache = _cache_path()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {"cookie": cookie, "expires_at": time.time() + 4 * 24 * 3600},
            ensure_ascii=True,
        )
        + "\n"
    )
    os.chmod(cache, 0o600)
    return cookie


def main() -> int:
    try:
        cookie = _valid_cached_session() or _login()
    except (RuntimeError, requests.RequestException) as exc:
        print(f"认证失败：{exc}", file=sys.stderr)
        return 1
    print(cookie)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
