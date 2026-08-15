"""上传文件名和类型校验。"""

from pathlib import Path

ALLOWED_RESUME_SUFFIXES = {".pdf", ".doc", ".docx"}


def is_allowed_resume(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_RESUME_SUFFIXES
