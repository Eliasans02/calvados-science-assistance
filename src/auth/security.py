"""Password hashing and token utilities."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from base64 import urlsafe_b64encode


def hash_password(password: str, iterations: int = 120_000) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${urlsafe_b64encode(salt).decode()}${urlsafe_b64encode(digest).decode()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    algorithm, iter_raw, salt_raw, digest_raw = encoded_hash.split("$", 3)
    if algorithm != "pbkdf2_sha256":
        return False
    iterations = int(iter_raw)
    salt = _decode_b64(salt_raw)
    expected = _decode_b64(digest_raw)
    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(expected, computed)


def _decode_b64(value: str) -> bytes:
    padding = "=" * ((4 - (len(value) % 4)) % 4)
    return __import__("base64").urlsafe_b64decode(value + padding)
