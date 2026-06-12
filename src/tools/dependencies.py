"""Auto-download and configure system dependencies for Friday tools.

Handles:
  - Poppler (required by pdf2image for PDF OCR)
  - Tesseract OCR (required by pytesseract for OCR)
  - Python packages (pip install if missing)
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "tools" / "bin"
POPPLER_DIR = TOOLS_DIR / "poppler"
POPPLER_BIN = POPPLER_DIR / "Library" / "bin"

POPPLER_API_URL = "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"


def _get_poppler_download_url() -> str:
    """Get the latest Poppler release download URL via GitHub API."""
    with urllib.request.urlopen(POPPLER_API_URL) as resp:
        data = json.loads(resp.read().decode())
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(".zip") and name.startswith("Release-"):
            return asset["browser_download_url"]
    raise RuntimeError("Could not find Poppler download URL")


_IMPORT_NAMES = {"Pillow": "PIL", "opencv-python-headless": "cv2"}
"""Package name → actual Python import name for packages where they differ."""


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)


def _add_to_path(path: str) -> None:
    current = os.environ.get("PATH", "")
    if path not in current:
        os.environ["PATH"] = path + os.pathsep + current


# ---- Poppler ----


def check_poppler() -> bool:
    """Check if Poppler binaries are accessible."""
    if shutil.which("pdftoppm") or shutil.which("pdfinfo"):
        return True
    if (POPPLER_BIN / "pdftoppm.exe").exists():
        _configure_poppler()
        return True
    return False


def _configure_poppler():
    _add_to_path(str(POPPLER_BIN))
    try:
        import pdf2image

        pdf2image.pdf2image.POPPLER_PATH = str(POPPLER_BIN)
    except ImportError:
        pass


def install_poppler(verbose: bool = True) -> bool:
    """Download Poppler and extract to tools/bin/poppler."""
    _ensure_dir(TOOLS_DIR)
    zip_path = TOOLS_DIR / "poppler-release.zip"

    try:
        url = _get_poppler_download_url()
        if verbose:
            print(f"Downloading Poppler from {url}...")
        _download(url, zip_path)

        if verbose:
            print("Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            extract_dir = TOOLS_DIR / "_poppler_extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            zf.extractall(extract_dir)

            extracted_items = list(extract_dir.iterdir())
            if extracted_items:
                src = extracted_items[0]
                if POPPLER_DIR.exists():
                    shutil.rmtree(POPPLER_DIR)
                shutil.copytree(src, POPPLER_DIR)

            shutil.rmtree(extract_dir)

        zip_path.unlink()
        _configure_poppler()

        if verbose:
            print(f"Poppler installed to {POPPLER_DIR}")
        return True

    except Exception as e:
        if verbose:
            print(f"Failed to install Poppler: {e}")
        return False


# ---- Tesseract ----


_TESSERACT_COMMON_PATHS = [
    r"C:\Program Files\Tesseract-OCR",
    r"C:\Program Files (x86)\Tesseract-OCR",
]
"""Common install directories for Tesseract on Windows."""


def _find_tesseract_install() -> str | None:
    """Return the directory path containing tesseract.exe, or None."""
    if shutil.which("tesseract"):
        return str(Path(shutil.which("tesseract")).parent)
    for p in _TESSERACT_COMMON_PATHS:
        if Path(p, "tesseract.exe").exists():
            return p
    return None


def check_tesseract() -> bool:
    """Check if Tesseract OCR is installed."""
    if _find_tesseract_install():
        _add_tesseract_to_path()
        return True
    return False


def install_tesseract(verbose: bool = True) -> bool:
    """Install Tesseract via winget, choco, or direct download."""
    existing = _find_tesseract_install()
    if existing:
        _add_tesseract_to_path()
        if verbose:
            print(f"Tesseract already installed at {existing}")
        return True

    if shutil.which("winget"):
        try:
            if verbose:
                print("Installing Tesseract via winget...")
            result = subprocess.run(
                ["winget", "install", "--id", "UB-Mannheim.TesseractOCR", "--silent", "--accept-package-agreements"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                _add_tesseract_to_path()
                if verbose:
                    print("Tesseract installed via winget.")
                return True
            if verbose:
                msg = result.stderr.strip() or result.stdout.strip() or "exit code {result.returncode}"
                print(f"winget failed: {msg}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    if shutil.which("choco"):
        try:
            if verbose:
                print("Installing Tesseract via Chocolatey...")
            result = subprocess.run(
                ["choco", "install", "tesseract", "-y"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                _add_tesseract_to_path()
                if verbose:
                    print("Tesseract installed via Chocolatey.")
                return True
            if verbose:
                msg = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
                print(f"Chocolatey failed: {msg}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    if verbose:
        print(
            "Could not auto-install Tesseract.\n"
            "  Install manually from: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "  Or run: winget install UB-Mannheim.TesseractOCR\n"
            "  Or run: choco install tesseract"
        )
    return False


def _add_tesseract_to_path():
    for p in _TESSERACT_COMMON_PATHS:
        if Path(p, "tesseract.exe").exists():
            _add_to_path(p)
            try:
                import pytesseract

                pytesseract.pytesseract.tesseract_cmd = str(Path(p, "tesseract.exe"))
            except ImportError:
                pass
            return


# ---- Python packages ----


def check_python_package(package_name: str) -> bool:
    """Check if a Python package is installed."""
    import_name = _IMPORT_NAMES.get(package_name, package_name.replace("-", "_"))
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False


def install_python_package(package_name: str, verbose: bool = True) -> bool:
    """Install a Python package via pip."""
    try:
        if verbose:
            print(f"Installing {package_name} via pip...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=not verbose,
            text=True,
            timeout=120,
        )
        return check_python_package(package_name)
    except (subprocess.TimeoutExpired, Exception) as e:
        if verbose:
            print(f"Failed to install {package_name}: {e}")
        return False


# ---- Bulk checks ----


def _get_tesseract_exe() -> str | None:
    """Get the full path to tesseract.exe, or None."""
    install = _find_tesseract_install()
    if install:
        exe = Path(install, "tesseract.exe")
        if exe.exists():
            return str(exe)
    return None


def _get_tessdata_dir() -> str | None:
    """Get the tessdata directory path, or None."""
    exe = _get_tesseract_exe()
    if not exe:
        return None
    # tessdata is typically <install_dir>/tessdata/
    candidate = Path(exe).parent / "tessdata"
    if candidate.exists():
        return str(candidate)
    return None


def check_tesseract_langs(langs: str) -> tuple[bool, list[str]]:
    """Check if Tesseract has the requested language packs installed.

    :param langs: Plus-separated language codes, e.g. "ben+ara+eng"
    :returns: (all_available, list of missing language codes)
    """
    exe = _get_tesseract_exe()
    if not exe:
        return False, langs.replace("+", ",").split(",")
    try:
        result = subprocess.run(
            [exe, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        available = set()
        for line in result.stdout.splitlines() + result.stderr.splitlines():
            line = line.strip()
            if line and not line.startswith("List") and not "Usage" in line and not ":" in line:
                available.add(line)
        lang_codes = [l.strip() for l in langs.replace("+", ",").split(",") if l.strip()]
        missing = [l for l in lang_codes if l not in available]
        return len(missing) == 0, missing
    except Exception:
        return False, langs.replace("+", ",").split(",")


def _get_local_tessdata() -> str:
    """Return a user-writable tessdata directory (under tools/bin/)."""
    local = TOOLS_DIR / "tessdata"
    local.mkdir(parents=True, exist_ok=True)
    return str(local)


def _ensure_tessdata_configured():
    """Make sure TESSDATA_PREFIX points to a writable directory with all needed languages.

    Falls back to a local tessdata dir under tools/bin/tessdata/ if the
    system tessdata dir is not writable. Copies eng.traineddata from
    the system so the local dir is self-contained.
    """
    if "TESSDATA_PREFIX" in os.environ and Path(os.environ["TESSDATA_PREFIX"]).exists():
        return
    sys_tessdata = _get_tessdata_dir()
    if sys_tessdata:
        try:
            test_file = Path(sys_tessdata, ".write_test")
            test_file.touch()
            test_file.unlink()
            os.environ.setdefault("TESSDATA_PREFIX", sys_tessdata)
            return
        except PermissionError:
            pass
    local = _get_local_tessdata()
    os.environ.setdefault("TESSDATA_PREFIX", local)
    # Copy eng.traineddata from system if not present locally
    eng_local = Path(local, "eng.traineddata")
    if not eng_local.exists() and sys_tessdata:
        eng_sys = Path(sys_tessdata, "eng.traineddata")
        if eng_sys.exists():
            try:
                shutil.copy2(str(eng_sys), str(eng_local))
            except PermissionError:
                pass
    # Also ensure pytesseract knows where tesseract.exe is
    exe = _get_tesseract_exe()
    if exe:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = exe
        except ImportError:
            pass


def install_tesseract_lang(lang_code: str, verbose: bool = True) -> bool:
    """Download and install a Tesseract language pack.

    Downloads the .traineddata file from the official tessdata repo.
    Tries system tessdata first, falls back to a local directory.

    :param lang_code: e.g. "ben", "ara", "eng"
    :returns: True if successful
    """
    _ensure_tessdata_configured()
    tessdata = os.environ.get("TESSDATA_PREFIX", "")
    if not tessdata:
        tessdata = _get_local_tessdata()

    dest = Path(tessdata, f"{lang_code}.traineddata")
    if dest.exists():
        if verbose:
            print(f"Language pack '{lang_code}' already installed.")
        return True

    url = f"https://github.com/tesseract-ocr/tessdata/raw/main/{lang_code}.traineddata"
    try:
        if verbose:
            print(f"Downloading language pack '{lang_code}'...")
        urllib.request.urlretrieve(url, dest)
        if verbose:
            print(f"Installed '{lang_code}' language pack at {dest}")
        return True
    except Exception as e:
        if verbose:
            print(f"Failed to download '{lang_code}': {e}")
        return False


def check_all() -> dict[str, bool]:
    """Check all known dependencies and return status dict."""
    return {
        "poppler": check_poppler(),
        "tesseract": check_tesseract(),
    }


def ensure_all(verbose: bool = True, auto_install: bool = False) -> list[str]:
    """Check all deps and optionally install missing ones.

    Returns list of still-missing dependency names.
    """
    deps = check_all()
    missing = [name for name, ok in deps.items() if not ok]

    if auto_install:
        for name in list(missing):
            if name == "poppler":
                if install_poppler(verbose=verbose):
                    missing.remove(name)
            elif name == "tesseract":
                if install_tesseract(verbose=verbose):
                    missing.remove(name)

    for pkg in ["opencv-python-headless", "pdf2image", "pytesseract", "Pillow"]:
        if not check_python_package(pkg):
            if verbose:
                print(f"Python package '{pkg}' not found.")
            if auto_install:
                install_python_package(pkg, verbose=verbose)
                if not check_python_package(pkg):
                    missing.append(pkg)
            else:
                missing.append(pkg)

    return missing
