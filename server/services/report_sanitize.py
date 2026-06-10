import re

from schemas.report import ConceptNode, ReportLLMOutput, WeakPoint

# 常见 emoji 区段（避免使用跨 CJK 的大范围区间）
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "]+",
    flags=re.UNICODE,
)
# 零宽字符与 BOM
_INVISIBLE_PATTERN = re.compile(r"[\u200b-\u200d\ufeff]")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def strip_emoji_and_symbols(text: str) -> str:
    """移除 emoji、装饰符号与零宽字符，保留中英文与常用标点。"""
    if not text:
        return ""
    cleaned = _INVISIBLE_PATTERN.sub("", text)
    cleaned = _EMOJI_PATTERN.sub("", cleaned)
    cleaned = _WHITESPACE_PATTERN.sub(" ", cleaned)
    return cleaned.strip()


def contains_emoji(text: str) -> bool:
    return bool(_EMOJI_PATTERN.search(text or ""))


def sanitize_report_llm_output(raw: ReportLLMOutput) -> ReportLLMOutput:
    """净化 LLM 报告全部文本字段为纯文本。"""
    weak_points = [
        WeakPoint(
            name=strip_emoji_and_symbols(item.name),
            reason=strip_emoji_and_symbols(item.reason),
        )
        for item in raw.weak_points
    ]
    concept_mastery = [
        ConceptNode(
            name=strip_emoji_and_symbols(item.name),
            mastery=item.mastery,
            related_question_count=item.related_question_count,
        )
        for item in raw.concept_mastery
    ]
    return raw.model_copy(
        update={
            "summary": strip_emoji_and_symbols(raw.summary),
            "suggestion": strip_emoji_and_symbols(raw.suggestion),
            "share_tagline": strip_emoji_and_symbols(raw.share_tagline),
            "weak_points": weak_points,
            "concept_mastery": concept_mastery,
        }
    )
