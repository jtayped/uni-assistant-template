"""
Ingestion pipeline orchestrator.
Takes a file from ingest/, classifies it, parses it, files it into vault/, updates the index.
"""
from pathlib import Path
from datetime import date
from typing import Optional
import shutil
import yaml

from config import settings


def _active_semester() -> str:
    import frontmatter
    active_file = settings.VAULT_PATH / "config" / "active.md"
    if active_file.exists():
        post = frontmatter.load(str(active_file))
        return post.metadata.get("semester_path", "unknown/semester-1")
    return "unknown/semester-1"


def _subject_dir(vault_path: Path, subject: str, semester: str) -> Path:
    return vault_path / "years" / semester / "subjects" / subject


def _write_exam_markdown(
    dest_dir: Path,
    pages,
    visual_pages: list,
    metadata: dict,
    pdf_filename: str,
) -> Path:
    """Write exam.md with extracted text + image references."""
    exam_md = dest_dir / "exam.md"
    images_dir = dest_dir / "images"
    images_dir.mkdir(exist_ok=True)

    subject = metadata.get("subject", "unknown")
    exam_type = metadata.get("exam_type", "unknown")
    semester_of_exam = metadata.get("exam_year", "unknown")
    exam_date = metadata.get("date", "unknown")

    front = {
        "type": "exam",
        "subject": subject,
        "semester_of_exam": semester_of_exam,
        "exam_type": exam_type,
        "date": exam_date,
        "source_pdf": f"raw/{pdf_filename}",
        "pages": len(pages),
        "visual_pages": visual_pages,
    }

    content_lines = [
        "---",
        yaml.dump(front, allow_unicode=True, default_flow_style=False).strip(),
        "---",
        "",
        f"# {subject.title()} — {exam_type.replace('_', ' ').title()} ({semester_of_exam})",
        "",
    ]

    for page in pages:
        content_lines.append(f"## Page {page.page_num}")
        if page.is_visual:
            img_name = f"page_{page.page_num:03d}.jpg"
            content_lines.append(f"![Page {page.page_num}](images/{img_name})")
            content_lines.append("")
        if page.text.strip():
            content_lines.append(page.text.strip())
            content_lines.append("")

    exam_md.write_text("\n".join(content_lines), encoding="utf-8")
    return exam_md


def _write_notes_markdown(
    dest_path: Path,
    content: str,
    metadata: dict,
) -> Path:
    """Write a notes markdown file with frontmatter."""
    front = {
        "type": "notes",
        "source": metadata.get("source", "unknown"),
        "quality": metadata.get("quality", "unknown"),
        "topic": metadata.get("topic", dest_path.stem),
        "subject": metadata.get("subject", "unknown"),
        "semester": metadata.get("semester", ""),
        "date_added": str(date.today()),
    }

    lines = [
        "---",
        yaml.dump(front, allow_unicode=True, default_flow_style=False).strip(),
        "---",
        "",
        content,
    ]

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text("\n".join(lines), encoding="utf-8")
    return dest_path


def ingest(file_path: str, metadata: dict, vault_path: str) -> str:
    """
    Full ingestion pipeline for a single file.
    Returns a status message describing what was done.
    """
    src = Path(file_path)
    vault = Path(vault_path)
    ext = src.suffix.lower()
    content_type = metadata.get("type", "unknown")
    subject = metadata.get("subject", "unknown")
    semester = metadata.get("semester") or _active_semester()

    subject_dir = _subject_dir(vault, subject, semester)
    subject_dir.mkdir(parents=True, exist_ok=True)

    steps = []

    if ext == ".pdf" and content_type == "exam":
        # PDF exam ingestion
        from ingestion.pdf_parser import extract_to_markdown

        exam_year = metadata.get("exam_year", "unknown")
        exam_type = metadata.get("exam_type", "unknown")
        folder_name = f"{exam_year}-{exam_type.replace('_', '-')}"
        exam_dir = subject_dir / "exams" / folder_name
        exam_dir.mkdir(parents=True, exist_ok=True)
        images_dir = exam_dir / "images"

        extraction = extract_to_markdown(str(src), str(images_dir))
        pages = extraction["pages"]
        visual_pages = extraction["visual_pages"]
        rendered = extraction["rendered_pages"]

        _write_exam_markdown(exam_dir, pages, visual_pages, metadata, src.name)

        # Copy raw PDF to subject/raw/ (gitignored, stays on VPS)
        raw_dir = subject_dir / "raw"
        raw_dir.mkdir(exist_ok=True)
        shutil.copy2(src, raw_dir / src.name)

        steps.append(f"Exam extracted: {len(pages)} pages, {len(rendered)} pages rendered as JPEG")
        steps.append(f"Filed to: {exam_dir.relative_to(vault)}")

    elif ext in (".md", ".txt") or content_type in ("notes", "slides", "textbook"):
        # Notes ingestion
        if ext == ".pdf":
            # Extract text from PDF for notes
            from ingestion.pdf_parser import parse_pdf
            pages = parse_pdf(str(src))
            content = "\n\n".join(p.text for p in pages if p.text.strip())
            content = f"[Extracted from PDF: {src.name}]\n\n{content}"
        else:
            content = src.read_text(encoding="utf-8", errors="replace")

        topic = metadata.get("topic") or src.stem
        dest = subject_dir / "content" / f"{topic.lower().replace(' ', '-')}.md"
        _write_notes_markdown(dest, content, metadata)
        steps.append(f"Notes filed to: {dest.relative_to(vault)}")

    else:
        steps.append(f"Unsupported type '{content_type}' for {ext} file. Manual filing needed.")
        return "\n".join(steps)

    # Update vector index
    try:
        from ingestion.indexer import upsert_document, parse_vault_file

        # Find the written markdown file for indexing
        written_mds = list(subject_dir.rglob("*.md"))
        newest = max(written_mds, key=lambda p: p.stat().st_mtime, default=None)
        if newest:
            records = parse_vault_file(newest, vault)
            from ingestion.indexer import upsert_document
            for record in records:
                upsert_document(record, str(settings.INDEX_PATH))
            steps.append(f"Index updated: {len(records)} chunks added")
    except Exception as e:
        steps.append(f"Index update skipped: {e}")

    # Remove from ingest/ drop zone
    src.unlink()
    steps.append(f"Removed from ingest/: {src.name}")

    return "\n".join(steps)
