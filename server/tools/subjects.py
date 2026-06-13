"""Subject tools — parse INDEX.md files, list subjects."""
from pathlib import Path
from typing import Optional
import frontmatter
from mcp_instance import mcp
from config import settings


def _find_subject_index(subject_id: str) -> Optional[Path]:
    """Search vault for a subject INDEX.md matching the given id/name."""
    pattern = f"**/subjects/{subject_id}/INDEX.md"
    matches = list(settings.VAULT_PATH.glob(pattern))
    if not matches:
        # Try case-insensitive partial match
        for p in settings.VAULT_PATH.glob("**/subjects/*/INDEX.md"):
            if subject_id.lower() in p.parent.name.lower():
                matches.append(p)
    return matches[0] if matches else None


def _active_semester() -> Optional[str]:
    """Read the active semester path from config/active.md."""
    active_file = settings.VAULT_PATH / "config" / "active.md"
    if not active_file.exists():
        return None
    post = frontmatter.load(str(active_file))
    return post.metadata.get("semester_path")


@mcp.tool()
def get_subject(subject_id: str) -> str:
    """
    Returns full subject information: marks schema, exam dates, deliverables, score so far.
    subject_id: the folder name of the subject (e.g. 'calculus', 'physics').
    """
    index_path = _find_subject_index(subject_id)
    if not index_path:
        return f"Subject '{subject_id}' not found in vault. Check the folder name or run list_subjects()."

    post = frontmatter.load(str(index_path))
    meta = post.metadata

    lines = [f"# {meta.get('name', subject_id)}", ""]

    grading = meta.get("grading", {})
    components = grading.get("components", [])
    if components:
        lines.append("## Grade Components")
        for c in components:
            score = c.get("score")
            score_str = f"{score}" if score is not None else "not yet"
            min_mark = c.get("minimum", 5.0)
            resit = "recuperable" if c.get("resittable", True) else "NOT recuperable"
            lines.append(
                f"- {c['name']} ({int(c['weight']*100)}%) — "
                f"score: {score_str} | min: {min_mark} | {resit} | date: {c.get('date', 'TBD')}"
            )

    resit = grading.get("resit", {})
    if resit:
        covers = ", ".join(resit.get("covers", []))
        lines.append(f"\nResit: {resit.get('date', 'TBD')} — covers: {covers}")

    deliverables = meta.get("deliverables", [])
    if deliverables:
        lines.append("\n## Deliverables")
        for d in deliverables:
            status = d.get("status", "unknown")
            lines.append(
                f"- {d['name']} — due: {d.get('due', 'TBD')} "
                f"({int(d.get('weight', 0)*100)}%) | min: {d.get('minimum', 5.0)} | {status}"
            )

    if post.content.strip():
        lines.append(f"\n## Notes\n{post.content.strip()}")

    return "\n".join(lines)


@mcp.tool()
def list_subjects(semester: Optional[str] = None) -> str:
    """
    Lists all subjects in the vault.
    semester: optional filter like '2025-2026/semester-1'. Defaults to active semester.
    """
    target = semester or _active_semester()
    if target:
        base = settings.VAULT_PATH / "years" / target / "subjects"
        glob_pattern = "*/INDEX.md"
    else:
        base = settings.VAULT_PATH / "years"
        glob_pattern = "**/subjects/*/INDEX.md"

    subjects = []
    for p in sorted(base.glob(glob_pattern)):
        try:
            post = frontmatter.load(str(p))
            name = post.metadata.get("name", p.parent.name)
            code = post.metadata.get("code", "")
            sem = post.metadata.get("semester", "")
            subjects.append(f"- **{name}** ({code}) — {sem} — path: {p.parent.name}")
        except Exception:
            subjects.append(f"- {p.parent.name} (parse error)")

    if not subjects:
        return "No subjects found. Run the init to set up your vault."
    return "## Subjects\n" + "\n".join(subjects)
