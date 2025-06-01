from datetime import datetime, timezone

import structlog

from config import get_async_logger

logger: structlog.stdlib.AsyncBoundLogger = get_async_logger()


def relative_diff(dt_str1, dt_str2):
    if not dt_str1 or not dt_str2:
        return ""
    dt1 = datetime.fromisoformat(dt_str1.replace("Z", "+00:00"))
    dt2 = datetime.fromisoformat(dt_str2.replace("Z", "+00:00"))
    diff = abs(dt1 - dt2)
    seconds = int(diff.total_seconds())
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    hours = hours % 24
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    minutes = minutes % 60
    if minutes > 0 and days == 0:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "0m"


def relative_time(dt_str):
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = int(diff.total_seconds())
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    months = days // 30

    if months > 0:
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif days > 0:
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"


def ellipsis(s, max_length):
    if not isinstance(s, str) or max_length < 4 or len(s) <= max_length:
        return s
    return s[: max_length - 1] + "…"
