"""Progress logging — append timestamped entries to campaign log.md."""
from datetime import datetime
from pathlib import Path
from typing import Optional
from mcp_instance import mcp
from config import settings


def _find_log(campaign_id: str) -> Optional[Path]:
    for p in settings.VAULT_PATH.glob("**/campaigns/*/log.md"):
        if campaign_id.lower() in p.parent.name.lower():
            return p
    return None


@mcp.tool()
def log_progress(
    subject: str,
    campaign: str,
    covered: str,
    outcome: str,
    notes: Optional[str] = None,
) -> str:
    """
    Appends a timestamped progress entry to the campaign log.
    Call this after EVERY response during a study session — do not wait until session end.

    subject: subject name (e.g. 'Calculus').
    campaign: campaign folder name (e.g. 'parcial-1-2026').
    covered: what was covered (e.g. '2024 Parcial 1 — Exercise 3').
    outcome: result ('completed', 'completed with help', 'attempted', 'stuck', 'skipped').
    notes: optional extra context.
    """
    log_path = _find_log(campaign)
    if not log_path:
        # Try to find campaign folder and create log.md
        for p in settings.VAULT_PATH.glob(f"**/campaigns/{campaign}"):
            log_path = p / "log.md"
            break
        if not log_path:
            return f"Campaign '{campaign}' not found. Cannot log progress."

    now = datetime.now()
    # Compute time since last entry for +Nmin display
    elapsed = ""
    if log_path.exists():
        stat = log_path.stat()
        minutes = int((now.timestamp() - stat.st_mtime) / 60)
        elapsed = f" | +{minutes}min"

    entry = f"\n## {now.strftime('%Y-%m-%d %H:%M')}{elapsed}\n\n"
    entry += f"**Subject:** {subject}\n"
    entry += f"**Campaign:** {campaign}\n"
    entry += f"**Covered:** {covered}\n"
    entry += f"**Outcome:** {outcome}\n"
    if notes:
        entry += f"**Notes:** {notes}\n"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

    return f"Progress logged to {log_path.name}"


@mcp.tool()
def get_session_log(subject_id: str, limit: int = 10) -> str:
    """
    Returns the most recent log entries for a subject's campaigns.
    Useful for resuming a session — shows what was last covered.

    subject_id: folder name of the subject.
    limit: max number of entries to return (default 10).
    """
    log_paths = list(settings.VAULT_PATH.glob(f"**/subjects/{subject_id}/campaigns/*/log.md"))
    if not log_paths:
        log_paths = [
            p for p in settings.VAULT_PATH.glob("**/campaigns/*/log.md")
            if subject_id.lower() in str(p).lower()
        ]

    if not log_paths:
        return f"No campaign logs found for '{subject_id}'."

    all_entries = []
    for log_path in log_paths:
        content = log_path.read_text(encoding="utf-8")
        # Split on entry headers (## DATE)
        parts = content.split("\n## ")
        entries = [p.strip() for p in parts if p.strip()]
        all_entries.extend([(log_path.parent.name, e) for e in entries])

    # Most recent first (entries are appended chronologically)
    all_entries.reverse()
    recent = all_entries[:limit]

    lines = [f"## Recent Log — {subject_id} (last {len(recent)} entries)"]
    for campaign_name, entry in recent:
        lines.append(f"\n### [{campaign_name}]\n{entry}")

    return "\n".join(lines)
