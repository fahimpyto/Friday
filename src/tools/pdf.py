from pathlib import Path

from src.tools.registry import tool


@tool
def read_pdf(path: str) -> str:
    """Extract text content from a PDF file.
    :param path: Absolute or relative path to the PDF file
    """
    path = Path(path).resolve()
    if not path.exists():
        return f"File not found: {path}"
    if not path.is_file():
        return f"Not a file: {path}"

    try:
        import fitz
    except ImportError:
        return "Error: PyMuPDF is not installed. Run: pip install PyMuPDF"

    try:
        doc = fitz.open(str(path))
        pages = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                pages.append(f"--- Page {page_num} ---\n{text}")

        doc.close()

        if not pages:
            return "(PDF appears to contain no extractable text)"

        return "\n".join(pages)
    except Exception as e:
        return f"Error reading PDF: {e}"
