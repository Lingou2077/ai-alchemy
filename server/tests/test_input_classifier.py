import pytest

from services.research.input_classifier import classify_input, extract_urls


def test_extract_urls():
    urls = extract_urls("阅读 https://example.com/a 和 https://foo.bar/b")
    assert len(urls) == 2


def test_classify_url_only():
    assert classify_input("https://en.wikipedia.org/wiki/Test") == "url"


def test_classify_keyword():
    assert classify_input("Harness Engineering") == "keyword"


def test_classify_mixed():
    text = "学习这个链接 https://example.com/doc 里的内容"
    assert classify_input(text) == "mixed"


def test_classify_long_text():
    assert classify_input("a" * 300) == "text"
