"""Marks tools — weighted average, minimum checks, resit logic, passing analysis."""
from pathlib import Path
from typing import Optional
import frontmatter
from mcp_instance import mcp
from config import settings


def _find_subject_index(subject_id: str) -> Optional[Path]:
    for p in settings.VAULT_PATH.glob("**/subjects/*/INDEX.md"):
        if subject_id.lower() in p.parent.name.lower():
            return p
    return None


@mcp.tool()
def compute_marks_status(subject_id: str) -> str:
    """
    Computes current grade status for a subject:
    - Current weighted average (from scored components)
    - Minimum needed on remaining components to pass (5.0 default)
    - Whether passing is still mathematically possible
    - Any components below minimum (global fail risk)
    - Resit coverage and recovery path

    subject_id: folder name of the subject.
    """
    index_path = _find_subject_index(subject_id)
    if not index_path:
        return f"Subject '{subject_id}' not found."

    post = frontmatter.load(str(index_path))
    meta = post.metadata
    grading = meta.get("grading", {})
    components = grading.get("components", [])
    passing_threshold = grading.get("passing", 5.0)
    resit = grading.get("resit", {})

    if not components:
        return f"No grade components defined for {subject_id}."

    total_weight = sum(c.get("weight", 0) for c in components)
    scored = [c for c in components if c.get("score") is not None]
    unscored = [c for c in components if c.get("score") is None]

    # Current weighted contribution from scored components
    current_contribution = sum(c["score"] * c["weight"] for c in scored)
    scored_weight = sum(c["weight"] for c in scored)
    unscored_weight = sum(c["weight"] for c in unscored)

    # Current average (only from scored)
    current_avg = (current_contribution / scored_weight) if scored_weight > 0 else None

    # Best possible grade (all remaining = 10)
    best_possible = current_contribution + (10 * unscored_weight)
    # Worst possible (all remaining = 0)
    worst_possible = current_contribution

    # What's needed on remaining components to reach passing
    needed_on_remaining = None
    if unscored_weight > 0:
        needed_total = passing_threshold * total_weight
        already_have = current_contribution
        needed_on_remaining = (needed_total - already_have) / unscored_weight

    can_pass = best_possible >= (passing_threshold * total_weight)

    # Minimum mark violations (below component minimum)
    violations = []
    for c in scored:
        min_mark = c.get("minimum", passing_threshold)
        if c["score"] < min_mark:
            can_resit = c.get("resittable", True)
            violations.append(
                f"  - **{c['name']}**: scored {c['score']} < minimum {min_mark} "
                f"({'can resit' if can_resit else 'CANNOT resit — GLOBAL FAIL'})"
            )

    lines = [f"## Marks Status: {meta.get('name', subject_id)}"]

    if scored:
        lines.append(f"\n**Scored so far:** {current_avg:.2f} avg from {int(scored_weight*100)}% of weight")
        for c in scored:
            lines.append(f"  - {c['name']}: {c['score']}/10 ({int(c['weight']*100)}%)")

    if unscored:
        lines.append(f"\n**Remaining:** {int(unscored_weight*100)}% of weight not yet scored")
        for c in unscored:
            lines.append(f"  - {c['name']} ({int(c['weight']*100)}%) — date: {c.get('date', 'TBD')}")

    lines.append(f"\n**Passing threshold:** {passing_threshold}/10")
    lines.append(f"**Best possible grade:** {best_possible:.2f}/10")

    if not can_pass:
        lines.append("\n⚠️ **Passing is MATHEMATICALLY IMPOSSIBLE.** Recommend redirecting study time.")
        if resit:
            resit_covers = ", ".join(resit.get("covers", []))
            lines.append(
                f"   Resit on {resit.get('date', 'TBD')} covers: {resit_covers}"
            )
    elif needed_on_remaining is not None:
        if needed_on_remaining > 10:
            lines.append(f"\n⚠️ Need {needed_on_remaining:.1f}/10 on remaining — impossible. Check resit options.")
        elif needed_on_remaining <= 0:
            lines.append(f"\n✅ Already passing. Need {max(0, needed_on_remaining):.1f}/10 on remaining to stay safe.")
        else:
            lines.append(f"\n📊 Need **{needed_on_remaining:.1f}/10** on remaining components to pass.")
    else:
        if current_contribution / total_weight >= passing_threshold:
            lines.append("\n✅ Already passing with current scores.")
        else:
            lines.append(f"\n❌ Below passing with {current_contribution/total_weight:.1f}/10.")

    if violations:
        lines.append("\n⛔ **Component minimum violations:**")
        lines.extend(violations)

    if resit and not violations:
        resit_covers = ", ".join(resit.get("covers", []))
        lines.append(
            f"\nResit available ({resit.get('date', 'TBD')}) — covers: {resit_covers}"
        )

    return "\n".join(lines)
