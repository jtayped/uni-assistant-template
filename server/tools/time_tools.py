"""Time tools — solves the morning/afternoon session problem."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from mcp_instance import mcp
from config import settings

_session_start: datetime | None = None


def _now() -> datetime:
    return datetime.now(tz=ZoneInfo(settings.TIMEZONE))


@mcp.tool()
def get_current_time() -> str:
    """
    Returns the real wall clock time and date from the server.
    Call this at the start of every session — never infer the time from conversation context.
    """
    global _session_start
    now = _now()
    if _session_start is None:
        _session_start = now
    return (
        f"Current time: {now.strftime('%H:%M')} "
        f"({now.strftime('%A, %B %d %Y')}) [{settings.TIMEZONE}]\n"
        f"Session started at: {_session_start.strftime('%H:%M')}"
    )


@mcp.tool()
def get_session_duration() -> str:
    """Returns how long the current session has been running."""
    if _session_start is None:
        return "Session start not recorded — call get_current_time() first."
    elapsed = _now() - _session_start
    minutes = int(elapsed.total_seconds() / 60)
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"Session duration: {hours}h {mins}min"
    return f"Session duration: {mins}min"
