"""Campaign tools — exercise queue, exam listing, campaign state management."""
from datetime import datetime
from pathlib import Path
from typing import Optional
import frontmatter
import yaml
from mcp_instance import mcp
from config import settings


def _find_campaign(campaign_id: str) -> Optional[Path]:
    for p in settings.VAULT_PATH.glob("**/campaigns/*/campaign.md"):
        if campaign_id.lower() in p.parent.name.lower():
            return p
    return None


@mcp.tool()
def list_exams(subject_id: str) -> str:
    """
    Lists all past exams for a subject, newest first.
    Use this to build study campaign exercise queues.

    subject_id: folder name of the subject.
    """
    exam_paths = sorted(
        settings.VAULT_PATH.glob(f"**/subjects/{subject_id}/exams/*/exam.md"),
        key=lambda p: p.parent.name,
        reverse=True,  # newest first (folder names include year)
    )
    if not exam_paths:
        # Try partial match
        exam_paths = sorted(
            [
                p for p in settings.VAULT_PATH.glob("**/exams/*/exam.md")
                if subject_id.lower() in str(p).lower()
            ],
            key=lambda p: p.parent.name,
            reverse=True,
        )

    if not exam_paths:
        return f"No exams found for '{subject_id}'. Ingest exam PDFs first."

    lines = [f"## Past Exams — {subject_id} (newest first)"]
    for p in exam_paths:
        try:
            post = frontmatter.load(str(p))
            meta = post.metadata
            exam_id = p.parent.name
            date = meta.get("date", "unknown date")
            exam_type = meta.get("exam_type", "unknown")
            pages = meta.get("pages", "?")
            visual = meta.get("visual_pages", [])
            lines.append(
                f"- **{exam_id}** — {exam_type} ({date}) | {pages} pages | "
                f"visual pages: {visual if visual else 'none'}"
            )
        except Exception:
            lines.append(f"- {p.parent.name} (parse error)")

    return "\n".join(lines)


@mcp.tool()
def get_campaign(campaign_id: str) -> str:
    """
    Returns current campaign state: exercise queue, progress, next action.

    campaign_id: partial folder name of the campaign (e.g. 'parcial-1-2026').
    """
    camp_path = _find_campaign(campaign_id)
    if not camp_path:
        return f"Campaign '{campaign_id}' not found. Use list_subjects() to find active campaigns."

    post = frontmatter.load(str(camp_path))
    meta = post.metadata

    subject = meta.get("subject", "unknown")
    target = meta.get("target_exam", "unknown")
    exam_date = meta.get("exam_date", "TBD")
    status = meta.get("status", "unknown")
    queue = meta.get("exams_queue", [])

    days_left = "unknown"
    if exam_date and exam_date != "TBD":
        try:
            d = datetime.strptime(str(exam_date), "%Y-%m-%d")
            days_left = max(0, (d - datetime.now()).days)
        except ValueError:
            pass

    lines = [
        f"## Campaign: {camp_path.parent.name}",
        f"Subject: {subject} | Target: {target} | Status: {status}",
        f"Exam date: {exam_date} ({days_left} days left)",
        "",
        "### Exercise Queue (newest exam first)",
    ]

    for exam in queue:
        exam_id = exam.get("id", "?")
        exam_status = exam.get("status", "not_started")
        done = exam.get("exercises_done", [])
        remaining = exam.get("exercises_remaining", [])

        if exam_status == "completed":
            lines.append(f"- ✅ {exam_id} — completed")
        elif exam_status == "in_progress":
            lines.append(
                f"- 🔄 {exam_id} — in progress | "
                f"done: {done} | remaining: {remaining}"
            )
        else:
            lines.append(f"- ⏳ {exam_id} — not started")

    if post.content.strip():
        lines.append(f"\n### Notes\n{post.content.strip()}")

    return "\n".join(lines)


@mcp.tool()
def update_campaign(
    campaign_id: str,
    exam_id: str,
    exercise_done: Optional[int] = None,
    exercise_status: Optional[str] = None,
    exam_status: Optional[str] = None,
) -> str:
    """
    Updates campaign progress: marks an exercise done, changes exam or campaign status.

    campaign_id: partial folder name of the campaign.
    exam_id: which exam in the queue to update (e.g. '2024-parcial-1').
    exercise_done: exercise number to mark as done (moves from remaining to done list).
    exercise_status: override status of the exercise ('done', 'skipped', 'flagged').
    exam_status: set the exam's overall status ('not_started', 'in_progress', 'completed').
    """
    camp_path = _find_campaign(campaign_id)
    if not camp_path:
        return f"Campaign '{campaign_id}' not found."

    post = frontmatter.load(str(camp_path))
    meta = post.metadata
    queue = meta.get("exams_queue", [])

    updated = False
    for exam in queue:
        if exam.get("id") == exam_id or exam_id.lower() in exam.get("id", "").lower():
            if exam_status:
                exam["status"] = exam_status
                updated = True
            if exercise_done is not None:
                remaining = exam.get("exercises_remaining", [])
                done = exam.get("exercises_done", [])
                if exercise_done in remaining:
                    remaining.remove(exercise_done)
                    done.append(exercise_done)
                    exam["exercises_remaining"] = remaining
                    exam["exercises_done"] = done
                    updated = True
                    if not remaining:
                        exam["status"] = "completed"
            break

    if not updated:
        return f"Exam '{exam_id}' not found in campaign queue."

    meta["exams_queue"] = queue
    # Write back
    with open(camp_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(yaml.dump(meta, allow_unicode=True, default_flow_style=False))
        f.write("---\n\n")
        f.write(post.content)

    return f"Campaign updated: {exam_id} in {camp_path.parent.name}"
