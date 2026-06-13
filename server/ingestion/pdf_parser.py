"""PDF parsing — text extraction + selective JPEG rendering for visual pages."""
from pathlib import Path
from typing import NamedTuple


class ParsedPage(NamedTuple):
    page_num: int        # 1-indexed
    text: str
    is_visual: bool      # True = render as JPEG
    image_count: int
    char_count: int


def parse_pdf(pdf_path: str) -> list[ParsedPage]:
    """
    Extract text and detect visual pages from a PDF.
    Visual pages = has embedded images OR very low text density (likely diagrams/formulas).
    """
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        images = page.get_images(full=False)
        image_count = len(images)
        char_count = len(text)

        # A page is "visual" if it has embedded images or almost no text
        is_visual = image_count > 0 or char_count < 80

        pages.append(ParsedPage(
            page_num=i + 1,
            text=text,
            is_visual=is_visual,
            image_count=image_count,
            char_count=char_count,
        ))

    doc.close()
    return pages


def render_page_jpeg(pdf_path: str, page_num: int, dpi: int = 150) -> bytes:
    """
    Render a single PDF page as JPEG bytes.
    page_num: 1-indexed.
    """
    import fitz

    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    jpeg_bytes = pix.tobytes("jpeg")
    doc.close()
    return jpeg_bytes


def extract_to_markdown(
    pdf_path: str,
    output_dir: str,
    render_visual_pages: bool = True,
    dpi: int = 150,
) -> dict:
    """
    Full extraction: text from all pages + JPEG renders for visual pages.
    Returns metadata about what was extracted.

    output_dir: where to write image files (exam's images/ folder).
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    pages = parse_pdf(pdf_path)
    visual_pages = [p.page_num for p in pages if p.is_visual]
    rendered = []

    if render_visual_pages:
        for page in pages:
            if page.is_visual:
                jpeg = render_page_jpeg(pdf_path, page.page_num, dpi)
                img_name = f"page_{page.page_num:03d}.jpg"
                img_path = output / img_name
                img_path.write_bytes(jpeg)
                rendered.append(page.page_num)

    return {
        "total_pages": len(pages),
        "visual_pages": visual_pages,
        "rendered_pages": rendered,
        "pages": pages,
    }
