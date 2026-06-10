from services.share_tagline import resolve_share_tagline


def test_resolve_share_tagline_keeps_valid_llm_output():
    result = resolve_share_tagline(
        "goroutine 已炼成",
        topic="Go 并发",
        quiz_status="completed",
        accuracy=90,
    )
    assert result == "goroutine 已炼成"


def test_resolve_share_tagline_truncates_long_output():
    result = resolve_share_tagline(
        "这是一句超过二十个字限制的炼金分享金句需要截断",
        topic="Go",
        quiz_status="completed",
        accuracy=90,
    )
    assert len(result) == 20


def test_resolve_share_tagline_failed_quiz():
    result = resolve_share_tagline(
        "",
        topic="Go 并发编程",
        quiz_status="failed",
        accuracy=20,
    )
    assert result == "灵韵散尽，下次必成"


def test_resolve_share_tagline_high_accuracy():
    result = resolve_share_tagline(
        None,
        topic="Go 并发",
        quiz_status="completed",
        accuracy=85,
    )
    assert "炼成成功" in result


def test_resolve_share_tagline_strips_emoji():
    result = resolve_share_tagline(
        "🎯 五题全中！goroutine 炼金",
        topic="Go 并发",
        quiz_status="completed",
        accuracy=100,
    )
    assert "🎯" not in result
    assert len(result) <= 20
    assert "五题全中" in result


def test_resolve_share_tagline_low_accuracy():
    result = resolve_share_tagline(
        "  ",
        topic="Go 并发",
        quiz_status="completed",
        accuracy=60,
    )
    assert "继续精炼" in result
