from __future__ import annotations

import io

import pytest

from fastapi import HTTPException, UploadFile

from app.constants import MAX_FILE_SIZE
from app.validation import read_and_validate_upload, EMPTY_FILE_DETAIL


@pytest.mark.asyncio
async def test_empty_file_rejected():
    file = UploadFile(filename="empty.png", file=io.BytesIO(b""))
    with pytest.raises(HTTPException) as exc_info:
        await read_and_validate_upload(file)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == EMPTY_FILE_DETAIL


@pytest.mark.asyncio
async def test_oversized_file_rejected():
    big_bytes = b"x" * (MAX_FILE_SIZE + 1)
    file = UploadFile(filename="big.png", file=io.BytesIO(big_bytes))
    with pytest.raises(HTTPException) as exc_info:
        await read_and_validate_upload(file, max_size=MAX_FILE_SIZE)
    assert exc_info.value.status_code == 413
