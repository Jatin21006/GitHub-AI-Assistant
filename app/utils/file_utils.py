"""File and path utility helpers for repository parsing."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".js", ".ts", ".tsx", ".java", ".cpp", ".c", ".h", ".html", ".css", ".md", ".json"}
)

IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {".git", "node_modules", "dist", "build", "venv", "__pycache__", ".next", "coverage"}
)

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".html": "html",
    ".css": "css",
    ".md": "markdown",
    ".json": "json",
}


def get_language(extension: str) -> str:
    """Map a file extension to a language label."""
    return EXTENSION_TO_LANGUAGE.get(extension.lower(), "unknown")


def is_ignored_path(relative_parts: tuple[str, ...]) -> bool:
    """Return True if any path segment is in the ignored directory set."""
    return any(part in IGNORED_DIR_NAMES for part in relative_parts)


def read_file_text(file_path: Path) -> str | None:
    """
    Read file contents as text with UTF-8 and fallback encodings.

    Returns None when the file cannot be decoded as text.
    """
    encodings = ("utf-8", "utf-8-sig", "latin-1")
    raw: bytes | None = None

    try:
        raw = file_path.read_bytes()
    except OSError:
        return None

    if b"\x00" in raw:
        return None

    for encoding in encodings:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    return None


def relative_file_path(repo_path: Path, file_path: Path) -> str:
    """Return a POSIX-style path relative to the repository root."""
    return file_path.relative_to(repo_path).as_posix()
