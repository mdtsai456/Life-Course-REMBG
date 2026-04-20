from __future__ import annotations

from app.constants import ALLOWED_IMAGE_MIME_TYPES, MAX_FILE_SIZE
from app.routes.images import _detect_image_type


class TestDetectImageType:
    def test_png(self):
        assert _detect_image_type(b"\x89PNG\r\n\x1a\nfoo") == "image/png"

    def test_jpeg(self):
        assert _detect_image_type(b"\xff\xd8\xfffoo") == "image/jpeg"

    def test_webp(self):
        data = b"RIFF" + b"\x00" * 4 + b"WEBP" + b"rest"
        assert _detect_image_type(data) == "image/webp"

    def test_unknown(self):
        assert _detect_image_type(b"random text") is None

    def test_short_bytes(self):
        assert _detect_image_type(b"") is None
        assert _detect_image_type(b"\x89P") is None


class TestConstants:
    def test_max_file_size_is_10mb(self):
        assert MAX_FILE_SIZE == 10 * 1024 * 1024

    def test_allowed_types(self):
        assert "image/png" in ALLOWED_IMAGE_MIME_TYPES
        assert "image/jpeg" in ALLOWED_IMAGE_MIME_TYPES
        assert "image/webp" in ALLOWED_IMAGE_MIME_TYPES
