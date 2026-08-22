"""
Password hashing (Argon2id) and opaque session token utilities.

Session design: the cookie holds a random 256-bit token. We store only
its SHA-256 hash server-side. Even a full DB read gives an attacker
nothing they can present as a valid session cookie.
"""
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()  # Argon2id by default in modern argon2-cffi


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, plain_password)
    except VerifyMismatchError:
        return False
    except Exception:
        # Any malformed-hash / library error is treated as "does not match"
        # rather than raised, so callers can't distinguish failure modes.
        return False


def generate_session_token() -> str:
    """Random, unguessable token to place in the session cookie."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
