"""
Server-side image validation. This is the authoritative check — the
frontend's pre-check is UX only.

Never trust:
- the client-supplied filename
- the client-supplied Content-Type header
- image metadata

Every check here operates on the actual bytes.
"""
import hashlib
import io

from PIL import Image

from app.core.config import get_settings

# Magic-byte signatures for the formats we accept. Checked before Pillow
# even attempts to decode, so we reject obviously-wrong files fast and
# don't feed the decoder more assumptions about "is this an image" than
# the raw bytes justify.
_SIGNATURES: dict[str, bytes] = {
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG\r\n\x1a\n",
    # WEBP: "RIFF"...."WEBP" — checked specially below.
}

Image.MAX_IMAGE_PIXELS = 40_000_000  # decompression-bomb guard (Pillow raises DecompressionBombError above this)


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _detect_real_mime(data: bytes) -> str | None:
    if data.startswith(_SIGNATURES["image/jpeg"]):
        return "image/jpeg"
    if data.startswith(_SIGNATURES["image/png"]):
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_and_load_image(data: bytes) -> tuple[str, int, int, str]:
    """
    Returns (real_mime_type, width, height, sha256_hex).
    Raises ImageValidationError on any failure. Never raises a raw
    library exception up to the API layer.
    """
    settings = get_settings()

    if len(data) == 0:
        raise ImageValidationError("EMPTY_FILE", "The uploaded file is empty.")

    if len(data) > settings.MAX_UPLOAD_BYTES:
        raise ImageValidationError(
            "IMAGE_TOO_LARGE",
            f"The uploaded image exceeds the {settings.MAX_UPLOAD_BYTES // (1024*1024)}MB limit.",
        )

    real_mime = _detect_real_mime(data)
    if real_mime is None or real_mime not in settings.ALLOWED_IMAGE_MIME_TYPES:
        raise ImageValidationError(
            "UNSUPPORTED_FORMAT",
            "Unsupported image format. Please upload a JPEG, PNG, or WEBP photo.",
        )

    try:
        image = Image.open(io.BytesIO(data))
        image.verify()  # structural check
        # verify() invalidates the file handle for further use; reopen to read dimensions safely.
        image2 = Image.open(io.BytesIO(data))
        width, height = image2.size
        image2.load()  # forces full decode; would raise on truncated/corrupt/decompression-bomb data
    except Exception as exc:  # Pillow raises many different exception types for bad images
        raise ImageValidationError(
            "CORRUPT_OR_MALFORMED_IMAGE",
            "The image could not be processed. It may be corrupted or in an unsupported format.",
        ) from exc

    if width > settings.MAX_IMAGE_DIMENSION_PX or height > settings.MAX_IMAGE_DIMENSION_PX:
        raise ImageValidationError(
            "IMAGE_DIMENSIONS_TOO_LARGE",
            f"Image dimensions exceed the {settings.MAX_IMAGE_DIMENSION_PX}px limit.",
        )
    if width < 32 or height < 32:
        raise ImageValidationError("IMAGE_TOO_SMALL", "Image is too small to analyze reliably.")

    digest = hashlib.sha256(data).hexdigest()
    return real_mime, width, height, digest


def strip_exif_and_reencode(data: bytes, mime_type: str) -> bytes:
    """Re-encodes the image without metadata (EXIF, GPS, etc.) for privacy."""
    image = Image.open(io.BytesIO(data))
    image = image.convert("RGB") if mime_type != "image/png" else image.convert("RGBA")
    out = io.BytesIO()
    fmt = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[mime_type]
    image.save(out, format=fmt)
    return out.getvalue()
