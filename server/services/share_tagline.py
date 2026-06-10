from services.report_sanitize import strip_emoji_and_symbols

_SHARE_TAGLINE_MAX_LEN = 20


def resolve_share_tagline(
    tagline: str | None,
    *,
    topic: str,
    quiz_status: str | None,
    accuracy: float,
) -> str:
    cleaned = strip_emoji_and_symbols(tagline or "")
    if cleaned:
        return cleaned[:_SHARE_TAGLINE_MAX_LEN]

    if quiz_status == "failed":
        return "灵韵散尽，下次必成"
    if accuracy >= 80:
        short_topic = topic[:10].rstrip()
        return f"{short_topic}炼成成功！"[:_SHARE_TAGLINE_MAX_LEN]
    short_topic = topic[:10].rstrip()
    return f"{short_topic}，继续精炼"[:_SHARE_TAGLINE_MAX_LEN]
