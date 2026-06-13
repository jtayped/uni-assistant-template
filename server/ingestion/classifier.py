"""Auto-classifier — infers file type, subject, exam year from filename and content."""
import re
from pathlib import Path
from typing import Optional


EXAM_KEYWORDS = {"parcial", "partial", "exam", "examen", "final", "resit", "recuperacion", "recuperació", "midterm", "test"}
NOTE_KEYWORDS = {"notes", "apunts", "apuntes", "teoria", "theory", "tema", "chapter", "unit"}
SLIDE_KEYWORDS = {"slides", "diapositives", "presentacion", "presentation", "lecture"}
TEXTBOOK_KEYWORDS = {"textbook", "libro", "llibre", "book", "manual"}


def auto_classify(file_path: str, content_preview: Optional[str] = None) -> dict:
    """
    Attempts to classify a file based on its name and optional content preview.
    Returns a dict with: type, subject, year, exam_type, confidence.
    confidence: 'high' (auto-ingest ok), 'low' (needs user confirmation).
    """
    name = Path(file_path).stem.lower()
    ext = Path(file_path).suffix.lower()

    result = {
        "type": "unknown",
        "subject": "unknown",
        "year": None,
        "exam_type": None,
        "confidence": "low",
    }

    # Year detection
    year_match = re.search(r"\b(20\d{2})\b", name)
    if year_match:
        result["year"] = year_match.group(1)

    # Type detection
    name_words = set(re.split(r"[-_\s.]", name))

    if name_words & EXAM_KEYWORDS:
        result["type"] = "exam"
        result["confidence"] = "high"

        # Exam type
        if any(k in name for k in ("parcial1", "parcial_1", "parcial-1", "midterm1")):
            result["exam_type"] = "parcial_1"
        elif any(k in name for k in ("parcial2", "parcial_2", "parcial-2", "midterm2")):
            result["exam_type"] = "parcial_2"
        elif "final" in name:
            result["exam_type"] = "final"
        elif any(k in name for k in ("resit", "recuperacion", "recuperació")):
            result["exam_type"] = "resit"

    elif name_words & NOTE_KEYWORDS:
        result["type"] = "notes"
        result["confidence"] = "high"

    elif name_words & SLIDE_KEYWORDS:
        result["type"] = "slides"
        result["confidence"] = "high"

    elif name_words & TEXTBOOK_KEYWORDS:
        result["type"] = "textbook"
        result["confidence"] = "high"

    # Subject detection (heuristic: first meaningful word that's not a type keyword)
    all_keywords = EXAM_KEYWORDS | NOTE_KEYWORDS | SLIDE_KEYWORDS | TEXTBOOK_KEYWORDS
    stop_words = all_keywords | {"the", "de", "el", "la", "les", "los", "and", "i", "y"}
    subject_candidates = [w for w in re.split(r"[-_\s]", name) if w not in stop_words and len(w) > 2 and not w.isdigit()]

    if subject_candidates:
        result["subject"] = subject_candidates[0]

    # Non-PDF files (markdown, text) are usually notes or normative
    if ext in (".md", ".txt") and result["type"] == "unknown":
        result["type"] = "notes"
        result["confidence"] = "high"

    return result
