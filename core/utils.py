"""
Utility helpers (time, formatting, etc.)
No business logic here.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from core.settings import MARKET_TIMEZONE


def now_utc() -> datetime:
    """
    Returns current UTC time (timezone-aware).
    """
    return datetime.now(timezone.utc)


def utc_to_market(dt: datetime) -> datetime:
    """
    Convert UTC datetime to market timezone (NYC).
    """
    if dt.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware (UTC)")

    return dt.astimezone(ZoneInfo(MARKET_TIMEZONE))


def format_price(value: float) -> str:
    return f"{value:.2f}"


def format_pnl(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"