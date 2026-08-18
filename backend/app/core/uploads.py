"""Shared validation for uploaded image payloads."""

from fastapi import UploadFile

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


class UploadTooLargeError(ValueError):
    """Raised when an upload exceeds the configured request limit."""


async def read_limited_upload(file: UploadFile) -> bytes:
    """Read at most the supported upload size plus one sentinel byte."""
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadTooLargeError("Image must not exceed 10 MiB")
    return content
