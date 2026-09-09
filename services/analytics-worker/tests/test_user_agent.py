from app.enrichment.user_agent import parse_user_agent

IPHONE_SAFARI = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
)
DESKTOP_CHROME = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"


def test_parse_desktop_chrome():
    result = parse_user_agent(DESKTOP_CHROME)
    assert result.device_type == "desktop"
    assert result.browser == "Chrome"
    assert result.os == "Windows"


def test_parse_iphone_safari():
    result = parse_user_agent(IPHONE_SAFARI)
    assert result.device_type == "mobile"
    assert result.browser == "Mobile Safari"
    assert result.os == "iOS"


def test_parse_bot():
    result = parse_user_agent(GOOGLEBOT)
    assert result.device_type == "bot"


def test_empty_string_returns_unknown():
    result = parse_user_agent("")
    assert result.device_type == "unknown"
    assert result.browser == "unknown"
    assert result.os == "unknown"


def test_garbage_string_does_not_raise():
    result = parse_user_agent("not a real user agent string !!! \x00\x01")
    assert result.device_type in {"unknown", "desktop", "bot", "mobile", "tablet"}
