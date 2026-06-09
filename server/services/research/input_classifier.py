import re

from schemas.research import InputKind

_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


def extract_urls(content: str) -> list[str]:
    return _URL_PATTERN.findall(content.strip())


def classify_input(content: str) -> InputKind:
    text = content.strip()
    urls = extract_urls(text)
    if not urls:
        return InputKind.keyword if len(text) <= 200 else InputKind.text
    remainder = text
    for url in urls:
        remainder = remainder.replace(url, " ")
    remainder = remainder.strip()
    if len(urls) == 1 and len(remainder) < 5:
        return InputKind.url
    return InputKind.mixed
