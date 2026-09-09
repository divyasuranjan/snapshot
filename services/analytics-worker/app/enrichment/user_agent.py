"""User-agent parsing: turns a raw UA string into device/browser/OS labels
for the dashboard's device breakdown."""

from __future__ import annotations

import logging

from user_agents import parse as parse_ua

from app.models import UAResult

logger = logging.getLogger(__name__)


def parse_user_agent(ua_string: str) -> UAResult:
    """Parses ua_string into device/browser/OS. Never raises: a missing or
    unparseable UA string (or a parsing library edge case) falls back to
    "unknown" fields rather than taking down event processing over what is,
    at most, a cosmetic enrichment gap."""

    if not ua_string:
        return UAResult()

    try:
        ua = parse_ua(ua_string)
    except Exception:
        logger.warning("user_agent_parse_failed", extra={"user_agent": ua_string[:200]})
        return UAResult()

    if ua.is_bot:
        device_type = "bot"
    elif ua.is_mobile:
        device_type = "mobile"
    elif ua.is_tablet:
        device_type = "tablet"
    elif ua.is_pc:
        device_type = "desktop"
    else:
        device_type = "unknown"

    browser = ua.browser.family or "unknown"
    os_name = ua.os.family or "unknown"

    return UAResult(device_type=device_type, browser=browser, os=os_name)
