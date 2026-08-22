"""
Object storage abstraction.

LocalObjectStorage is used for local development (writes under a
private, non-web-served directory). The interface is deliberately
S3-shaped so a real S3/MinIO-backed implementation can replace it later
without touching calling code.
"""
import os
import uuid
from abc import ABC, abstractmethod

_STORAGE_ROOT = os.environ.get("LOCAL_STORAGE_ROOT", "/home/claude/tesseractis/backend/_private_storage")


class ObjectStorage(ABC):
    @abstractmethod
    def put_object(self, data: bytes, extension: str) -> str:
        """Stores bytes under a random key and returns that key. Never uses
        the caller-supplied filename."""
        raise NotImplementedError

    @abstractmethod
    def get_object(self, key: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def delete_object(self, key: str) -> None:
        raise NotImplementedError


class LocalObjectStorage(ObjectStorage):
    def __init__(self, root: str = _STORAGE_ROOT):
        self.root = root
        os.makedirs(self.root, mode=0o700, exist_ok=True)

    def _safe_path(self, key: str) -> str:
        # Defense in depth: even though we generate keys ourselves,
        # reject anything that isn't a bare filename (no path traversal).
        if "/" in key or "\\" in key or key in ("..", "."):
            raise ValueError("Invalid object key.")
        return os.path.join(self.root, key)

    def put_object(self, data: bytes, extension: str) -> str:
        safe_ext = "".join(c for c in extension if c.isalnum())[:8] or "bin"
        key = f"{uuid.uuid4().hex}.{safe_ext}"
        path = self._safe_path(key)
        with open(path, "wb") as f:
            f.write(data)
        os.chmod(path, 0o600)
        return key

    def get_object(self, key: str) -> bytes:
        path = self._safe_path(key)
        with open(path, "rb") as f:
            return f.read()

    def delete_object(self, key: str) -> None:
        path = self._safe_path(key)
        if os.path.exists(path):
            os.remove(path)


_storage_instance: ObjectStorage | None = None


def get_object_storage() -> ObjectStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = LocalObjectStorage()
    return _storage_instance
