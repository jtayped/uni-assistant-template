"""Ingest tools — classify, parse, and file new content into the vault."""
from pathlib import Path
from typing import Optional
from mcp_instance import mcp
from config import settings


@mcp.tool()
def process_ingest_folder() -> str:
    """
    Scans vault/ingest/ for new files and reports what was found.
    The agent should then classify each ambiguous file by asking the user,
    and call ingest_file() for each one with the confirmed metadata.

    Returns a list of files waiting to be ingested with auto-classification guesses.
    """
    ingest_dir = settings.VAULT_PATH / "ingest"
    files = [f for f in ingest_dir.iterdir() if f.is_file() and f.name != ".gitkeep"]

    if not files:
        return "Ingest folder is empty. Drop files into vault/ingest/ to process them."

    from ingestion.classifier import auto_classify

    lines = ["## Files in vault/ingest/\n"]
    for f in sorted(files):
        guess = auto_classify(str(f))
        confidence = guess.get("confidence", "low")
        file_type = guess.get("type", "unknown")
        year = guess.get("year")
        subject_guess = guess.get("subject", "unknown")

        if confidence == "high":
            lines.append(
                f"- **{f.name}** → auto-classified: {file_type}"
                + (f" | year: {year}" if year else "")
                + f" | subject guess: {subject_guess} ✅ (auto-ingest OK)"
            )
        else:
            lines.append(
                f"- **{f.name}** → unclear: {file_type}"
                + (f" | year: {year}" if year else "")
                + " ⚠️ (needs your confirmation)"
            )

    lines.append(
        "\nFor each file, call ingest_file(file_path, metadata) with the confirmed classification."
    )
    return "\n".join(lines)


@mcp.tool()
def ingest_file(
    file_name: str,
    subject: str,
    content_type: str,
    semester: Optional[str] = None,
    exam_type: Optional[str] = None,
    exam_year: Optional[str] = None,
    source: Optional[str] = None,
    quality: Optional[str] = None,
    topic: Optional[str] = None,
) -> str:
    """
    Ingests a file from vault/ingest/ into the vault with the given metadata.
    Handles PDF parsing, JPEG rendering for visual pages, markdown extraction, and index update.

    file_name: filename in vault/ingest/ (e.g. 'calculus-parcial1-2024.pdf').
    subject: subject folder name (e.g. 'calculus').
    content_type: 'exam', 'notes', 'slides', 'textbook', 'normative'.
    semester: e.g. '2025-2026/semester-1'. Defaults to active semester.
    exam_type: 'parcial_1', 'parcial_2', 'final', 'resit' — required if type='exam'.
    exam_year: year of the exam (e.g. '2024') — required if type='exam'.
    source: 'own_notes', 'borrowed', 'internet', 'textbook', 'slides'.
    quality: 'complete', 'partial', 'unknown'.
    topic: topic name for notes files.
    """
    src = settings.VAULT_PATH / "ingest" / file_name
    if not src.exists():
        return f"File '{file_name}' not found in vault/ingest/."

    from ingestion.pipeline import ingest

    metadata = {
        "subject": subject,
        "type": content_type,
        "semester": semester,
        "exam_type": exam_type,
        "exam_year": exam_year,
        "source": source or "unknown",
        "quality": quality or "unknown",
        "topic": topic,
    }

    result = ingest(str(src), metadata, str(settings.VAULT_PATH))
    return result


@mcp.tool()
def rebuild_index() -> str:
    """
    Full rebuild of the vector search index from all vault markdown files.
    Call this after:
    - Directly editing vault files (INDEX.md, notes, etc.)
    - A batch ingest session (multiple ingest_file() calls)
    - Any time search results seem stale or missing content.
    """
    from ingestion.indexer import build_index

    result = build_index(str(settings.VAULT_PATH), str(settings.INDEX_PATH))
    return (
        f"Index rebuilt: {result['files']} files → {result['indexed']} chunks indexed."
        if result["status"] == "ok"
        else f"Index rebuild result: {result}"
    )
