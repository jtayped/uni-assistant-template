"""Render tool — on-demand PDF page rendering when raw PDF is available on VPS."""
import base64
from pathlib import Path
from typing import Optional
from mcp_instance import mcp
from config import settings


def _find_raw_pdf(doc_id: str) -> Optional[Path]:
    """Find the raw PDF for a given document id (exam folder name)."""
    # Raw PDFs live in subject/raw/ (gitignored, VPS only)
    for p in settings.VAULT_PATH.glob("**/raw/*.pdf"):
        if doc_id.lower() in p.stem.lower():
            return p
    # Also check by exam folder name
    for p in settings.VAULT_PATH.glob(f"**/exams/{doc_id}/exam.md"):
        raw_dir = p.parent.parent.parent / "raw"
        for pdf in raw_dir.glob("*.pdf"):
            if doc_id.split("-")[0] in pdf.stem:
                return pdf
    return None


@mcp.tool()
def render_page(doc_id: str, page_number: int, dpi: int = 150) -> str:
    """
    Renders a specific page of a PDF as a JPEG image (base64 encoded).
    Only works if the raw PDF is present on the VPS (vault/SUBJECT/raw/).
    Falls back gracefully if the PDF is not available.

    doc_id: exam folder name or partial PDF filename (e.g. '2024-parcial-1').
    page_number: 1-indexed page to render.
    dpi: render resolution (default 150 — ~50KB/page).
    """
    pdf_path = _find_raw_pdf(doc_id)
    if not pdf_path:
        return (
            f"Raw PDF for '{doc_id}' not found on this machine. "
            "Use the pre-rendered images in the exam's images/ folder instead, "
            "or check the exam.md for extracted text."
        )

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        if page_number < 1 or page_number > len(doc):
            return f"Page {page_number} out of range. Document has {len(doc)} pages."

        page = doc[page_number - 1]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        jpeg_bytes = pix.tobytes("jpeg")
        b64 = base64.b64encode(jpeg_bytes).decode("ascii")
        size_kb = len(jpeg_bytes) // 1024

        return (
            f"Page {page_number} of {doc_id} rendered ({size_kb}KB).\n"
            f"data:image/jpeg;base64,{b64}"
        )

    except Exception as e:
        return f"Render failed for {doc_id} page {page_number}: {e}"
