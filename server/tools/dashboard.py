"""Dashboard tool — session start overview of everything urgent."""
from datetime import datetime
from pathlib import Path
from typing import Optional
import frontmatter
from mcp_instance import mcp
from config import settings


@mcp.tool()
def get_dashboard() -> str:
    """
    Returns the session dashboard: active campaigns, days to exams,
    deliverables due within 14 days, and a suggested next action.
    Call this at the start of every session, right after get_current_time().
    """
    now = datetime.now()
    lines = [f"# Dashboard — {now.strftime('%A %d %B %Y, %H:%M')}\n"]

    # --- Active campaigns ---
    campaigns = list(settings.VAULT_PATH.glob("**/campaigns/*/campaign.md"))
    active = []
    for camp_path in campaigns:
        try:
            post = frontmatter.load(str(camp_path))
            meta = post.metadata
            if meta.get("status") != "active":
                continue

            subject = meta.get("subject", "unknown")
            target = meta.get("target_exam", "?")
            exam_date_str = str(meta.get("exam_date", ""))
            days_left = "?"

            if exam_date_str:
                try:
                    exam_date = datetime.strptime(exam_date_str, "%Y-%m-%d")
                    days_left = max(0, (exam_date - now).days)
                except ValueError:
                    pass

            queue = meta.get("exams_queue", [])
            total_exams = len(queue)
            completed_exams = sum(1 for e in queue if e.get("status") == "completed")

            active.append({
                "name": camp_path.parent.name,
                "subject": subject,
                "target": target,
                "days_left": days_left,
                "progress": f"{completed_exams}/{total_exams} exams",
                "exam_date": exam_date_str,
            })
        except Exception:
            continue

    # Sort by days left (most urgent first)
    active.sort(key=lambda c: c["days_left"] if isinstance(c["days_left"], int) else 999)

    if active:
        lines.append("## Active Campaigns")
        for c in active:
            urgency = ""
            if isinstance(c["days_left"], int):
                if c["days_left"] <= 3:
                    urgency = " 🔴"
                elif c["days_left"] <= 7:
                    urgency = " 🟡"
            lines.append(
                f"- **{c['subject']}** — {c['target']} | "
                f"{c['days_left']} days left{urgency} | "
                f"progress: {c['progress']}"
            )
    else:
        lines.append("## Active Campaigns\nNone. Start a new campaign with the subject's exam list.")

    # --- Deliverables due soon ---
    lines.append("\n## Deliverables Due (next 14 days)")
    upcoming = []
    for index_path in settings.VAULT_PATH.glob("**/subjects/*/INDEX.md"):
        try:
            post = frontmatter.load(str(index_path))
            subject_name = post.metadata.get("name", index_path.parent.name)
            deliverables = post.metadata.get("deliverables", [])
            for d in deliverables:
                if d.get("status") in ("submitted", "done"):
                    continue
                due_str = str(d.get("due", ""))
                if not due_str:
                    continue
                try:
                    due = datetime.strptime(due_str, "%Y-%m-%d")
                    days_until = (due - now).days
                    if 0 <= days_until <= 14:
                        upcoming.append({
                            "subject": subject_name,
                            "name": d.get("name", "?"),
                            "due": due_str,
                            "days": days_until,
                            "status": d.get("status", "not_started"),
                        })
                except ValueError:
                    continue
        except Exception:
            continue

    upcoming.sort(key=lambda d: d["days"])
    if upcoming:
        for d in upcoming:
            urgency = " 🔴" if d["days"] <= 2 else (" 🟡" if d["days"] <= 5 else "")
            lines.append(
                f"- **{d['subject']}** — {d['name']} | "
                f"due: {d['due']} ({d['days']} days){urgency} | {d['status']}"
            )
    else:
        lines.append("No deliverables due in the next 14 days.")

    # --- High-yield signal ---
    lines.append("\n## High-Yield Topics")
    lines.append(_detect_high_yield())

    # --- Suggestion ---
    lines.append("\n## Suggested Next Action")
    if active:
        most_urgent = active[0]
        lines.append(
            f"Continue **{most_urgent['subject']}** campaign ({most_urgent['target']}) — "
            f"{most_urgent['days_left']} days to exam."
        )
    elif upcoming:
        lines.append(f"Work on deliverable: **{upcoming[0]['name']}** ({upcoming[0]['subject']}) — due in {upcoming[0]['days']} days.")
    else:
        lines.append("No urgent campaigns or deliverables. Start a new campaign or review completed material.")

    return "\n".join(lines)


def _detect_high_yield(min_occurrences: int = 3) -> str:
    """Find topics appearing in 3+ recent exams per subject."""
    import re
    from collections import defaultdict

    topic_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for exam_path in settings.VAULT_PATH.glob("**/exams/*/exam.md"):
        try:
            post = frontmatter.load(str(exam_path))
            subject = post.metadata.get("subject", "unknown")
            content = post.content

            # Extract exercise headers and topic keywords (simple heuristic)
            headers = re.findall(r"(?:#{1,3})\s+(.+)", content)
            for h in headers:
                topic_counts[subject][h.strip().lower()] += 1
        except Exception:
            continue

    results = []
    for subject, topics in topic_counts.items():
        high_yield = [t for t, count in topics.items() if count >= min_occurrences]
        if high_yield:
            results.append(f"**{subject}:** {', '.join(high_yield[:5])}")

    return "\n".join(results) if results else "Not enough exam data yet to detect high-yield topics."
