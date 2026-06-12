from pathlib import Path
from PIL import Image

from src.tools.dependencies import check_poppler, check_tesseract, check_tesseract_langs, install_tesseract_lang, _ensure_tessdata_configured
from src.tools.registry import tool

# Auto-configure Poppler on import if available locally
check_poppler()


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


def _extract_text_ocr(path: str, lang: str = "eng") -> list[tuple[int, str]]:
    """Extract text via OCR (pdf2image + pytesseract)."""
    from pdf2image import convert_from_path
    import pytesseract

    _ensure_tessdata_configured()

    images = convert_from_path(str(path), dpi=600)
    pages = []
    for page_num, img in enumerate(images, 1):
        text = pytesseract.image_to_string(img, lang=lang)
        if text.strip():
            pages.append((page_num, text.strip()))
    return pages


@tool
def read_pdf(path: str, lang: str = "eng") -> str:
    """Extract text content from a PDF file. Uses OCR fallback for scanned/image-based PDFs.
    :param path: Absolute or relative path to the PDF file
    :param lang: Language(s) for OCR, e.g. "eng", "ben", "ara", "ben+ara+eng" (default: "eng")
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
                if not check_poppler():
                    return (
                        "Poppler not found — needed for PDF OCR.\n"
                        "  Run: python -c \"from src.tools.dependencies import install_poppler; install_poppler()\"\n"
                        "  Or run: python src\\main.py --setup"
                    )
                if not check_tesseract():
                    return (
                        "Tesseract OCR engine not found.\n"
                        "  Run: python -c \"from src.tools.dependencies import install_tesseract; install_tesseract()\"\n"
                        "  Or run: python src\\main.py --setup"
                    )
                all_ok, missing = check_tesseract_langs(lang)
                if not all_ok:
                    print(f"Missing Tesseract language pack(s): {', '.join(missing)}. Downloading...")
                    for lc in missing:
                        install_tesseract_lang(lc)
                    all_ok, missing = check_tesseract_langs(lang)
                    if not all_ok:
                        return (
                            f"Could not install Tesseract language pack(s): {', '.join(missing)}\n"
                            f"  Download manually from: https://github.com/tesseract-ocr/tessdata\n"
                            f"  Place .traineddata files in your Tesseract tessdata folder."
                        )
                pages = _extract_text_ocr(path, lang=lang)
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
                if "tesseract" in str(e).lower() or "poppler" in str(e).lower():
                    return (
                        f"{'Poppler' if 'poppler' in str(e).lower() else 'Tesseract'} not found.\n"
                        f"  Run: python src\\main.py --setup\n"
                        f"  Or install manually from:\n"
                        f"    Poppler: https://github.com/oschwartz10612/poppler-windows/releases\n"
                        f"    Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
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
