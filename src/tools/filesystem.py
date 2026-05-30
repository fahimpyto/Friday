import os
import difflib
from pathlib import Path

from src.tools.registry import tool


@tool
def read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read contents of a file with optional line range.
    :param path: Absolute or relative path to the file
    :param offset: Line number to start from (0-indexed)
    :param limit: Maximum number of lines to read
    """
    path = Path(path).resolve()
    if not path.exists():
        return f"File not found: {path}"
    if not path.is_file():
        return f"Not a file: {path}"

    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    selected = lines[offset:offset + limit]
    return "".join(selected) or "(empty file)"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file, creating parent directories if needed.
    :param path: Absolute or relative path to the file
    :param content: Text content to write
    """
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Written {len(content)} characters to {path}"


@tool
def edit_file(path: str, old_string: str, new_string: str) -> str:
    """Search and replace text in a file. Shows a diff of changes.
    :param path: Absolute or relative path to the file
    :param old_string: Text to search for (must match exactly)
    :param new_string: Text to replace with
    """
    path = Path(path).resolve()
    if not path.exists():
        return f"File not found: {path}"

    with open(path, encoding="utf-8", errors="replace") as f:
        original = f.read()

    if old_string not in original:
        return f"Error: old_string not found in {path}"

    count = original.count(old_string)
    updated = original.replace(old_string, new_string)

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=str(path),
        tofile=str(path),
    )
    diff_text = "".join(diff)

    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)

    return f"Replaced {count} occurrence(s) in {path}\n{diff_text}"


@tool
def list_directory(path: str = ".") -> str:
    """List all entries in a directory.
    :param path: Directory path (default: current directory)
    """
    path = Path(path).resolve()
    if not path.exists():
        return f"Directory not found: {path}"
    if not path.is_dir():
        return f"Not a directory: {path}"

    entries = []
    for entry in sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())):
        suffix = "/" if entry.is_dir() else ""
        entries.append(f"{entry.name}{suffix}")

    if not entries:
        return "(empty directory)"

    return "\n".join(entries)


@tool
def glob_files(pattern: str, path: str = ".") -> str:
    """Find files matching a glob pattern.
    :param path: Root directory to search in
    :param pattern: Glob pattern (e.g. "**/*.py", "src/**/*.ts")
    """
    root = Path(path).resolve()
    if not root.exists():
        return f"Directory not found: {path}"

    matches = [str(p.relative_to(root)) for p in sorted(root.rglob(pattern)) if p.is_file()]

    if not matches:
        return f"No files matching '{pattern}' in {path}"

    return "\n".join(matches)


@tool
def grep_content(pattern: str, path: str = ".", include: str = "") -> str:
    """Search file contents using a regular expression.
    :param pattern: Regex pattern to search for
    :param path: Root directory to search in
    :param include: File glob to filter (e.g. "*.py", "*.{ts,tsx}")
    """
    import re

    root = Path(path).resolve()
    if not root.exists():
        return f"Directory not found: {path}"

    results = []
    for file_path in root.rglob(include) if include else root.rglob("*"):
        if not file_path.is_file():
            continue
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), 1):
                if re.search(pattern, line):
                    rel = file_path.relative_to(root)
                    results.append(f"{rel}:{i}: {line.strip()}")
        except Exception:
            pass

    if not results:
        return f"No matches for '{pattern}'"

    return "\n".join(results[:200])
