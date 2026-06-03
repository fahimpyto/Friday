from pathlib import Path

from src.tools.registry import tool


def _extract_text_fitz(path: str) -> list[tuple[int, str]]:
    """Extract text via PyMuPDF. Returns list of (page_num, text)."""
    import fitz

    doc = fitz.open(str(path))
    pages = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        if text.strip():
            pages.append((page_num, text))
    doc.close()
    return pages


def _extract_text_ocr(path: str) -> list[tuple[int, str]]:
    """Extract text via OCR (pdf2image + pytesseract)."""
    from pdf2image import convert_from_path
    import pytesseract

    images = convert_from_path(str(path), dpi=300)
    pages = []
    for page_num, img in enumerate(images, 1):
        text = pytesseract.image_to_string(img)
        if text.strip():
            pages.append((page_num, text.strip()))
    return pages


@tool
def read_pdf(path: str) -> str:
    """Extract text content from a PDF file. Uses OCR fallback for scanned/image-based PDFs.
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
        pages = _extract_text_fitz(path)

        if not pages:
            try:
                pages = _extract_text_ocr(path)
            except ImportError as e:
                missing = str(e).split("'")[1] if "'" in str(e) else str(e)
                return (
                    f"No extractable text found and OCR is not available.\n"
                    f"Install missing packages: pip install pdf2image pytesseract Pillow\n"
                    f"Also install Tesseract OCR engine:\n"
                    f"  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                    f"  macOS:   brew install tesseract\n"
                    f"  Linux:   sudo apt install tesseract-ocr"
                )
            except Exception as e:
                if "tesseract" in str(e).lower():
                    return (
                        f"Tesseract OCR engine not found.\n"
                        f"Install it manually:\n"
                        f"  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                        f"  macOS:   brew install tesseract\n"
                        f"  Linux:   sudo apt install tesseract-ocr"
                    )
                return f"OCR error: {e}"

        if not pages:
            return "(PDF appears to contain no extractable text)"

        result = []
        for page_num, text in pages:
            result.append(f"--- Page {page_num} ---\n{text}")
        return "\n".join(result)
    except Exception as e:
        return f"Error reading PDF: {e}"
