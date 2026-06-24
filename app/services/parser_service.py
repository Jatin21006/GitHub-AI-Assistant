"""Source code parser and chunker for cloned repositories."""

from __future__ import annotations

import logging
import os
from collections import Counter
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models.schemas import ParserStats
from app.utils.file_utils import (
    SUPPORTED_EXTENSIONS,
    get_language,
    is_ignored_path,
    read_file_text,
    relative_file_path,
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200


def scan_repository(repo_path: Path, repository_name: str) -> tuple[list[Path], int]:
    """
    Recursively scan a repository for supported source files.

    Args:
        repo_path: Absolute path to the cloned repository root.
        repository_name: Repository identifier in owner/name format.

    Returns:
        A tuple of (matched file paths, skipped file count).
    """
    repo_path = repo_path.resolve()
    if not repo_path.is_dir():
        raise ValueError(f"Repository path does not exist: {repo_path}")

    matched_files: list[Path] = []
    files_skipped = 0

    logger.info("Scanning repository '%s' at %s", repository_name, repo_path)

    for root, dirnames, filenames in os.walk(repo_path):
        dirnames[:] = [name for name in dirnames if name not in _ignored_dirnames_set()]

        current_dir = Path(root)
        for filename in filenames:
            file_path = current_dir / filename
            relative_parts = file_path.relative_to(repo_path).parts

            if is_ignored_path(relative_parts):
                files_skipped += 1
                logger.debug("Skipping ignored path: %s", file_path)
                continue

            extension = file_path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                files_skipped += 1
                logger.debug("Skipping unsupported extension (%s): %s", extension, file_path)
                continue

            matched_files.append(file_path)

    logger.info(
        "Scan complete for '%s': %d file(s) matched, %d skipped",
        repository_name,
        len(matched_files),
        files_skipped,
    )
    return matched_files, files_skipped


def load_documents(
    repo_path: Path,
    repository_name: str,
    file_paths: list[Path],
) -> tuple[list[Document], int]:
    """
    Load repository files into LangChain Document objects.

    Args:
        repo_path: Absolute path to the cloned repository root.
        repository_name: Repository identifier in owner/name format.
        file_paths: Files to load, typically from scan_repository().

    Returns:
        A tuple of (documents, load_skipped_count).
    """
    repo_path = repo_path.resolve()
    documents: list[Document] = []
    load_skipped = 0

    logger.info("Loading %d file(s) for '%s'", len(file_paths), repository_name)

    for file_path in file_paths:
        extension = file_path.suffix.lower()
        rel_path = relative_file_path(repo_path, file_path)
        language = get_language(extension)

        content = read_file_text(file_path)
        if content is None:
            load_skipped += 1
            logger.warning("Skipped unreadable file: %s", rel_path)
            continue

        if not content.strip():
            load_skipped += 1
            logger.debug("Skipped empty file: %s", rel_path)
            continue

        metadata = {
            "repository_name": repository_name,
            "file_path": rel_path,
            "file_name": file_path.name,
            "language": language,
            "extension": extension,
        }
        documents.append(Document(page_content=content, metadata=metadata))
        logger.debug("Loaded document: %s (%s)", rel_path, language)

    logger.info(
        "Loaded %d document(s) for '%s' (%d skipped)",
        len(documents),
        repository_name,
        load_skipped,
    )
    return documents, load_skipped


def chunk_documents(documents: list[Document]) -> list[Document]:
    """
    Split documents into chunks using RecursiveCharacterTextSplitter.

    Each chunk receives a unique chunk_id and retains source file metadata.

    Args:
        documents: LangChain Document objects from load_documents().

    Returns:
        Chunked LangChain Document objects.
    """
    if not documents:
        logger.info("No documents to chunk")
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    logger.info("Chunking %d document(s) (size=%d, overlap=%d)", len(documents), CHUNK_SIZE, CHUNK_OVERLAP)

    chunks: list[Document] = []
    per_file_counters: Counter[str] = Counter()

    for document in documents:
        file_path = document.metadata["file_path"]
        split_chunks = splitter.split_documents([document])

        for split_chunk in split_chunks:
            chunk_index = per_file_counters[file_path]
            per_file_counters[file_path] += 1

            repository_name = split_chunk.metadata["repository_name"]
            split_chunk.metadata["chunk_id"] = f"{repository_name}:{file_path}:{chunk_index}"
            split_chunk.metadata["chunk_index"] = chunk_index
            chunks.append(split_chunk)

    logger.info("Created %d chunk(s) from %d document(s)", len(chunks), len(documents))
    return chunks


def parse_repository(repo_path: Path, repository_name: str) -> tuple[list[Document], ParserStats]:
    """
    Run the full parse pipeline: scan, load, and chunk.

    Args:
        repo_path: Absolute path to the cloned repository root.
        repository_name: Repository identifier in owner/name format.

    Returns:
        A tuple of (chunked documents, parser statistics).
    """
    file_paths, scan_skipped = scan_repository(repo_path, repository_name)
    documents, load_skipped = load_documents(repo_path, repository_name, file_paths)
    chunks = chunk_documents(documents)

    language_distribution = Counter(doc.metadata["language"] for doc in documents)

    stats = ParserStats(
        files_processed=len(documents),
        files_skipped=scan_skipped + load_skipped,
        total_documents=len(documents),
        total_chunks=len(chunks),
        language_distribution=dict(sorted(language_distribution.items())),
    )

    logger.info(
        "Parse complete for '%s': %d files, %d chunks, languages=%s",
        repository_name,
        stats.files_processed,
        stats.total_chunks,
        stats.language_distribution,
    )
    return chunks, stats


def _ignored_dirnames_set() -> frozenset[str]:
    from app.utils.file_utils import IGNORED_DIR_NAMES

    return IGNORED_DIR_NAMES
