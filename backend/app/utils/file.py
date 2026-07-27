"""Attachment file handling (manual 12).

Files are stored under <upload_dir>/<YYYY>/<MM>/<business_type>/ with a random
UUID filename. Original filenames are never used on disk.
"""
import os
import uuid
from datetime import date

from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import file_too_large

ALLOWED_EXT = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".pdf", ".docx", ".xlsx", ".xls",
    ".txt", ".log", ".csv",
}
# per-type upper bounds (MB)
EXT_LIMIT_MB = {
    frozenset({".jpg", ".jpeg", ".png", ".webp"}): 10,
    frozenset({".pdf", ".docx", ".xlsx", ".xls"}): 20,
    frozenset({".txt", ".log", ".csv"}): 20,
}


def _ext_limit(ext: str) -> int:
    for group, limit in EXT_LIMIT_MB.items():
        if ext in group:
            return limit
    return settings.max_upload_mb


def _validate(ext: str, size: int):
    if ext not in ALLOWED_EXT:
        from app.core.exceptions import bad_request

        raise bad_request(f"不支持的文件类型: {ext}")
    limit = _ext_limit(ext)
    if size > limit * 1024 * 1024:
        raise file_too_large(f"文件超过 {limit}MB 限制")


async def save_upload(
    file: UploadFile,
    business_type: str,
    business_id: int,
    upload_dir: str | None = None,
) -> dict:
    upload_dir = upload_dir or settings.upload_dir
    original = file.filename or "file"
    ext = os.path.splitext(original)[1].lower()
    content = await file.read()
    _validate(ext, len(content))

    rel_dir = os.path.join(str(date.today().year), f"{date.today().month:02d}", business_type)
    abs_dir = os.path.join(upload_dir, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    stored = uuid.uuid4().hex + ext
    abs_path = os.path.join(abs_dir, stored)
    with open(abs_path, "wb") as f:
        f.write(content)

    return {
        "original_name": original,
        "stored_name": stored,
        "file_path": os.path.join(rel_dir, stored),
        "mime_type": file.content_type or _guess_mime(ext),
        "size": len(content),
        "business_type": business_type,
        "business_id": business_id,
    }


def _guess_mime(ext: str) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".txt": "text/plain", ".log": "text/plain", ".csv": "text/csv",
    }.get(ext, "application/octet-stream")
