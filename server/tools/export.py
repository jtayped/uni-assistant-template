"""Export tool — converts markdown informe drafts to PDF via pandoc."""
import subprocess
from pathlib import Path
from mcp_instance import mcp
from config import settings


@mcp.tool()
def export_markdown_to_pdf(file_path: str) -> str:
    """
    Converts a markdown file to PDF using pandoc.
    Outputs the PDF alongside the source markdown file.
    Designed for informe drafts in project/_ai/ folders.

    file_path: path relative to vault root (e.g. 'years/2025-2026/semester-1/subjects/prog/projects/lab1/_ai/informe_draft.md').
    """
    full_path = settings.VAULT_PATH / file_path
    if not full_path.exists():
        return f"File not found: {file_path}"

    if full_path.suffix.lower() != ".md":
        return "Only markdown (.md) files can be exported."

    output_path = full_path.with_suffix(".pdf")

    try:
        result = subprocess.run(
            [
                "pandoc",
                str(full_path),
                "-o", str(output_path),
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=2cm",
                "-V", "fontsize=11pt",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            # Try without xelatex (fallback to default)
            result = subprocess.run(
                ["pandoc", str(full_path), "-o", str(output_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

        if result.returncode != 0:
            return f"Pandoc failed:\n{result.stderr}"

        size_kb = output_path.stat().st_size // 1024
        return (
            f"Exported: {output_path.name} ({size_kb}KB)\n"
            f"Location: {file_path.replace('.md', '.pdf')}\n"
            "Both .md and .pdf files kept. NEVER include the _ai/ folder in your submission archive."
        )

    except FileNotFoundError:
        return "pandoc not found. Install it: apt install pandoc"
    except subprocess.TimeoutExpired:
        return "pandoc timed out. File may be too large."
    except Exception as e:
        return f"Export failed: {e}"
