"""
Utility helpers (time, formatting, etc.)
No business logic here.
"""
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from core.settings import MARKET_TIMEZONE

def now_utc() -> datetime:
    """
    Returns current UTC time (timezone-aware).
    """
    return datetime.now(timezone.utc)


def ensure_utc_aware(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware UTC.
    """

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def utc_to_market(dt: datetime) -> datetime:
    """
    Convert UTC datetime to market timezone (NYC).
    """

    dt = ensure_utc_aware(dt)

    return dt.astimezone(ZoneInfo(MARKET_TIMEZONE))


def utc_to_market_time(dt: datetime) -> datetime:
    """
    Alias for utc_to_market.
    """

    return utc_to_market(dt)


def format_duration_from_minutes(minutes: int) -> str:
    """
    Format duration as:
    2d 05h 31m
    """

    if minutes < 0:
        minutes = 0

    days = minutes // (24 * 60)
    hours = (minutes % (24 * 60)) // 60
    mins = minutes % 60

    return f"{days}d {hours:02d}h {mins:02d}m"


def format_price(value: float) -> str:
    """
    Format price to 2 decimal places.
    """

    return f"{value:.2f}"


def format_pnl(value: float) -> str:
    """
    Format PnL with sign.
    """
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"

def normalize_timestamp_to_utc(dt) -> datetime:
    """
    Convert pandas/numpy/python datetime to timezone-aware UTC datetime.
    """
    return pd.to_datetime(dt, utc=True).to_pydatetime()


def format_market_datetime(dt) -> str:
    """
    Format any timestamp-like object in market timezone.
    """
    utc_dt = normalize_timestamp_to_utc(dt)
    market_dt = utc_to_market(utc_dt)
    return market_dt.strftime("%Y-%m-%d %H:%M:%S %Z")