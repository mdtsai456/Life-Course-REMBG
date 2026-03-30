"""Constants for image upload and validation."""

from __future__ import annotations

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
WEBP_MAGIC_RIFF = b"RIFF"
WEBP_MAGIC_TAG = b"WEBP"

FILE_TOO_LARGE_DETAIL = f"檔案過大，最大允許 {MAX_FILE_SIZE // (1024 * 1024)} MB。"

# Allowed MIME types for image uploads (remove-background)
ALLOWED_IMAGE_MIME_TYPES: frozenset[str] = frozenset(
    {"image/png", "image/jpeg", "image/webp"}
)
