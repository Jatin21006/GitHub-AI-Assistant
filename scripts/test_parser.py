"""Test script for repository parsing and chunking."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.services.clone_service import CloneError, CloneService
from app.services.parser_service import chunk_documents, load_documents, parse_repository, scan_repository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

SMALL_REPO_URL = "https://github.com/octocat/Hello-World"
LARGE_REPO_URL = "https://github.com/psf/requests"


def _print_stats(label: str, stats) -> None:
    print(f"\n=== {label} ===")
    print(f"Files processed:      {stats.files_processed}")
    print(f"Files skipped:        {stats.files_skipped}")
    print(f"Total documents:      {stats.total_documents}")
    print(f"Total chunks:         {stats.total_chunks}")
    print("Language breakdown:")
    if stats.language_distribution:
        for language, count in stats.language_distribution.items():
            print(f"  {language}: {count}")
    else:
        print("  (none)")


def _validate_chunks(chunks, repository_name: str) -> None:
    required_metadata = {"repository_name", "file_path", "file_name", "language", "extension", "chunk_id"}

    if not chunks:
        return

    for chunk in chunks:
        missing = required_metadata - set(chunk.metadata.keys())
        if missing:
            raise AssertionError(f"Chunk missing metadata keys: {missing}")

        if chunk.metadata["repository_name"] != repository_name:
            raise AssertionError("Chunk repository_name mismatch")

        if not chunk.page_content.strip():
            raise AssertionError(f"Empty chunk content for {chunk.metadata['chunk_id']}")


def test_repository(clone_service: CloneService, github_url: str, label: str) -> int:
    print(f"\n--- Testing parser on {label} ({github_url}) ---")

    try:
        clone_result = clone_service.clone(github_url)
    except CloneError as exc:
        print(f"Clone failed: {exc}")
        return 1

    repo_path = clone_result.local_path
    repository_name = clone_result.repository_name

    file_paths, scan_skipped = scan_repository(repo_path, repository_name)
    documents, load_skipped = load_documents(repo_path, repository_name, file_paths)
    chunks = chunk_documents(documents)

    _, stats = parse_repository(repo_path, repository_name)

    _print_stats(label, stats)
    _validate_chunks(chunks, repository_name)

    print(f"Scan skipped:         {scan_skipped}")
    print(f"Load skipped:         {load_skipped}")

    if stats.files_processed != len(documents):
        print("Error: files_processed does not match loaded documents.")
        return 1

    if stats.total_chunks != len(chunks):
        print("Error: total_chunks does not match chunk list length.")
        return 1

    if stats.files_processed > 0 and stats.total_chunks == 0:
        print("Error: documents loaded but no chunks created.")
        return 1

    for chunk in chunks:
        chunk_id = chunk.metadata["chunk_id"]
        expected_prefix = f"{repository_name}:"
        if not chunk_id.startswith(expected_prefix):
            print(f"Error: invalid chunk_id format: {chunk_id}")
            return 1

    print(f"{label} parser test passed.")
    return 0


def main() -> int:
    settings = get_settings()
    clone_service = CloneService(settings)

    small_result = test_repository(clone_service, SMALL_REPO_URL, "octocat/Hello-World")
    if small_result != 0:
        return small_result

    large_result = test_repository(clone_service, LARGE_REPO_URL, "psf/requests (larger repo)")
    if large_result != 0:
        return large_result

    print("\nAll parser tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
