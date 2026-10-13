"""Time helpers. Everything in Tafi is stored and compared in UTC."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Now, timezone-aware."""
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """SQLite hands back naive datetimes; treat them as UTC."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def is_expired(value: datetime) -> bool:
    """True when the moment has passed."""
    return as_utc(value) < utcnow()
