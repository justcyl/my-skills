#!/usr/bin/env python3
"""
从 macOS Edge 浏览器自动提取指定域名的 Cookie。

用法：
    python edge_cookies.py <domain>
    python edge_cookies.py overleaf.cyl.qzz.io

输出 Cookie 头部字符串（可直接赋值给 OVERLEAF_COOKIE）。

原理：
  1. 从 macOS Keychain 获取 Edge Safe Storage 密码
  2. 用 PBKDF2 派生 AES-128-CBC 密钥
  3. 复制 Edge Cookies SQLite 数据库（避免锁冲突）
  4. 查询目标域名的 cookie 行，解密 encrypted_value
  5. 拼接为标准 Cookie 头部字符串
"""

import os
import sys
import shutil
import sqlite3
import subprocess
import tempfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding


EDGE_COOKIES_PATH = os.path.expanduser(
    "~/Library/Application Support/Microsoft Edge/Default/Cookies"
)
KEYCHAIN_SERVICE = "Microsoft Edge Safe Storage"
KEYCHAIN_ACCOUNT = "Microsoft Edge"

# Chromium on macOS: PBKDF2 with salt=b'saltysalt', iterations=1003, key_length=16
SALT = b"saltysalt"
ITERATIONS = 1003
KEY_LENGTH = 16


def get_keychain_password() -> str:
    """从 macOS Keychain 获取 Edge Safe Storage 密码。"""
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-w",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            KEYCHAIN_ACCOUNT,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"错误：无法从 Keychain 获取 Edge 密码。\n{result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout.strip()


def derive_key(password: str) -> bytes:
    """用 PBKDF2 派生 AES 密钥。"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=KEY_LENGTH,
        salt=SALT,
        iterations=ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def decrypt_cookie_value(encrypted_value: bytes, key: bytes) -> str:
    """解密 Chromium cookie 的 encrypted_value。

    支持两种格式：
      v10 (Edge/macOS): 3-byte tag + 16-byte nonce + 16-byte IV + AES-128-CBC ciphertext
      v10 (Chrome/macOS legacy): 3-byte tag + AES-128-CBC ciphertext, IV = b' ' * 16
    """
    if not encrypted_value:
        return ""

    version_tag = encrypted_value[:3]

    if version_tag == b"v10":
        data = encrypted_value[3:]

        # Edge/macOS: 16-byte nonce + 16-byte IV + ciphertext
        # 尝试用 bytes[16:32] 作为 IV 解密 bytes[32:]
        if len(data) > 32:
            iv = data[16:32]
            ciphertext = data[32:]
            try:
                cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
                decryptor = cipher.decryptor()
                pt = decryptor.update(ciphertext) + decryptor.finalize()
                unpadder = padding.PKCS7(128).unpadder()
                plaintext = unpadder.update(pt) + unpadder.finalize()
                result = plaintext.decode("utf-8")
                if result.isprintable():
                    return result
            except Exception:
                pass

        # Legacy Chrome/macOS: IV = 16 个空格
        iv = b" " * 16
        ciphertext = data
        try:
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            pt = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(pt) + unpadder.finalize()
            return plaintext.decode("utf-8")
        except Exception:
            pass

    # 未加密或未知格式
    return encrypted_value.decode("utf-8", errors="replace")


def extract_cookies(domain: str) -> str:
    """提取指定域名的所有 cookie，返回 Cookie 头部字符串。"""
    if not os.path.exists(EDGE_COOKIES_PATH):
        print(f"错误：未找到 Edge Cookies 数据库：{EDGE_COOKIES_PATH}", file=sys.stderr)
        sys.exit(1)

    password = get_keychain_password()
    key = derive_key(password)

    # 复制数据库以避免 Edge 运行时的锁冲突
    tmp_dir = tempfile.mkdtemp()
    tmp_db = os.path.join(tmp_dir, "Cookies")
    try:
        shutil.copy2(EDGE_COOKIES_PATH, tmp_db)

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()

        # 匹配域名：host_key 可能是 .example.com 或 example.com
        cursor.execute(
            """
            SELECT name, value, encrypted_value
            FROM cookies
            WHERE host_key = ? OR host_key = ?
            ORDER BY name
            """,
            (domain, f".{domain}"),
        )

        cookies = []
        for name, value, encrypted_value in cursor.fetchall():
            if value:
                cookie_value = value
            elif encrypted_value:
                cookie_value = decrypt_cookie_value(encrypted_value, key)
            else:
                continue
            cookies.append(f"{name}={cookie_value}")

        conn.close()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if not cookies:
        print(f"警告：未找到域名 '{domain}' 的任何 cookie。请确认已在 Edge 中登录 Overleaf。", file=sys.stderr)
        sys.exit(1)

    return "; ".join(cookies)


def main():
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <domain>", file=sys.stderr)
        print(f"示例: {sys.argv[0]} overleaf.mycompany.com", file=sys.stderr)
        sys.exit(1)

    domain = sys.argv[1]
    cookie_str = extract_cookies(domain)
    print(cookie_str)


if __name__ == "__main__":
    main()
