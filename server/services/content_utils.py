from fastapi import HTTPException

from config import settings


def normalize_content(content: str) -> tuple[str, bool]:
    text = content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="请输入学习内容")
    truncated = False
    if len(text) > settings.content_max_length:
        raise HTTPException(status_code=400, detail="内容超过 5000 字上限")
    if len(text) > settings.content_truncate_length:
        text = text[: settings.content_truncate_length]
        truncated = True
    return text, truncated
