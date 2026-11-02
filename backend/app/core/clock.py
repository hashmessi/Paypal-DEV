"""Injectable clock interface and implementations for deterministic testing and demo simulation."""

from datetime import date, datetime, timedelta, timezone
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Protocol for getting the current date and time."""

    def now(self) -> datetime:
        """Return timezone-aware current UTC datetime."""
        ...

    def today(self) -> date:
        """Return current date."""
        ...


class SystemClock:
    """Standard system clock returning real UTC time."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def today(self) -> date:
        return datetime.now(timezone.utc).date()


class FixedClock:
    """Frozen clock returning a constant fixed datetime for deterministic tests."""

    def __init__(self, frozen_at: datetime) -> None:
        if frozen_at.tzinfo is None:
            self._frozen = frozen_at.replace(tzinfo=timezone.utc)
        else:
            self._frozen = frozen_at

    def now(self) -> datetime:
        return self._frozen

    def today(self) -> date:
        return self._frozen.date()

    def advance(self, delta: timedelta) -> None:
        self._frozen += delta


class DemoOffsetClock:
    """Clock that applies a dynamic offset to system time for simulating expiration and delays."""

    def __init__(self, offset: timedelta = timedelta(0)) -> None:
        self._offset = offset

    @property
    def offset(self) -> timedelta:
        return self._offset

    def set_offset(self, delta: timedelta) -> None:
        self._offset = delta

    def set_offset_days(self, days: int) -> None:
        self._offset = timedelta(days=days)

    def now(self) -> datetime:
        return datetime.now(timezone.utc) + self._offset

    def today(self) -> date:
        return (datetime.now(timezone.utc) + self._offset).date()

