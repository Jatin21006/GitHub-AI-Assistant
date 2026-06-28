"""Test suite for app.services.vector_store module."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.services.vector_store import (
    VectorStoreError,
    build_vector_store,
    load_vector_store,
    save_vector_store,
)


def _sample_documents() -> list[Document]:
    """Return a small set of LangChain Documents for testing."""
    return [
        Document(
            page_content=(
                "def hello_world():\n"
                "    \"\"\"Print a greeting.\"\"\"\n"
                "    print('Hello, World!')\n"
            ),
            metadata={
                "file_path": "src/greeting.py",
                "file_type": "python",
                "language": "python",
            },
        ),
        Document(
            page_content=(
                "class Calculator:\n"
                "    def add(self, a: int, b: int) -> int:\n"
                "        return a + b\n"
                "\n"
                "    def subtract(self, a: int, b: int) -> int:\n"
                "        return a - b\n"
            ),
            metadata={
                "file_path": "src/calculator.py",
                "file_type": "python",
                "language": "python",
            },
        ),
        Document(
            page_content=(
                "# Project README\n"
                "\n"
                "This project demonstrates a simple Python application\n"
                "with a greeting module and a calculator module.\n"
            ),
            metadata={
                "file_path": "README.md",
                "file_type": "markdown",
                "language": "markdown",
            },
        ),
    ]


FAKE_EMBEDDING_DIM = 8


def _fake_embed_documents(texts: list[str]) -> list[list[float]]:
    """Return deterministic fake embeddings for testing."""
    return [[float(i)] * FAKE_EMBEDDING_DIM for i, _ in enumerate(texts)]


def _fake_embed_query(text: str) -> list[float]:
    """Return a deterministic fake query embedding."""
    return [0.5] * FAKE_EMBEDDING_DIM


def test_build_vector_store_creates_index() -> None:
    """build_vector_store should create a FAISS index from sample documents."""
    documents = _sample_documents()

    with patch(
        "app.services.vector_store._create_embeddings"
    ) as mock_create_embeddings:
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents = _fake_embed_documents
        mock_embeddings.embed_query = _fake_embed_query
        mock_create_embeddings.return_value = mock_embeddings

        vector_store = build_vector_store(documents)

    # The FAISS index should have been populated
    assert vector_store is not None
    # At least one vector must exist
    assert vector_store.index.ntotal > 0
    print(f"  [PASS] FAISS index built with {vector_store.index.ntotal} vector(s)")


def test_build_vector_store_preserves_metadata() -> None:
    """Every chunk must contain file_path, file_type, and chunk_id metadata."""
    documents = _sample_documents()

    with patch(
        "app.services.vector_store._create_embeddings"
    ) as mock_create_embeddings:
        mock_embeddings = MagicMock()
        mock_embeddings.embed_documents = _fake_embed_documents
        mock_embeddings.embed_query = _fake_embed_query
        mock_create_embeddings.return_value = mock_embeddings

        vector_store = build_vector_store(documents)

    # Inspect stored metadata via the docstore
    for doc_id in vector_store.index_to_docstore_id.values():
        doc = vector_store.docstore.search(doc_id)
        assert hasattr(doc, "metadata"), "Chunk is missing metadata"
        assert "file_path" in doc.metadata, f"Chunk {doc_id} missing file_path"
        assert "file_type" in doc.metadata, f"Chunk {doc_id} missing file_type"
        assert "chunk_id" in doc.metadata, f"Chunk {doc_id} missing chunk_id"

    print("  [PASS] All chunks preserve file_path, file_type, and chunk_id")


def test_save_and_load_vector_store() -> None:
    """A saved vector store should be loadable and contain the same vectors."""
    documents = _sample_documents()
    tmp_dir = Path(tempfile.mkdtemp())

    try:
        with patch(
            "app.services.vector_store._create_embeddings"
        ) as mock_create_embeddings:
            mock_embeddings = MagicMock()
            mock_embeddings.embed_documents = _fake_embed_documents
            mock_embeddings.embed_query = _fake_embed_query
            mock_create_embeddings.return_value = mock_embeddings

            original = build_vector_store(documents)
            original_count = original.index.ntotal

            save_path = save_vector_store(original, tmp_dir)
            assert save_path.is_dir(), "Save path should be a directory"

            index_file = save_path / "index.faiss"
            assert index_file.exists(), "FAISS index file should exist"
            print(f"  [PASS] Saved index to {save_path}")

            loaded = load_vector_store(save_path)
            assert loaded.index.ntotal == original_count, (
                f"Expected {original_count} vectors but got {loaded.index.ntotal}"
            )
            print(f"  [PASS] Loaded index with {loaded.index.ntotal} vector(s)")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_build_vector_store_empty_raises() -> None:
    """build_vector_store should raise VectorStoreError for empty input."""
    try:
        build_vector_store([])
        assert False, "Should have raised VectorStoreError"
    except VectorStoreError:
        print("  [PASS] Correctly raised VectorStoreError for empty documents")


def test_load_vector_store_missing_path_raises() -> None:
    """load_vector_store should raise VectorStoreError for a non-existent path."""
    try:
        load_vector_store("/non/existent/path")
        assert False, "Should have raised VectorStoreError"
    except VectorStoreError:
        print("  [PASS] Correctly raised VectorStoreError for missing path")


if __name__ == "__main__":
    tests = [
        ("build_vector_store creates index", test_build_vector_store_creates_index),
        ("build_vector_store preserves metadata", test_build_vector_store_preserves_metadata),
        ("save and load vector store", test_save_and_load_vector_store),
        ("build_vector_store empty raises", test_build_vector_store_empty_raises),
        ("load_vector_store missing path raises", test_load_vector_store_missing_path_raises),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        print(f"\nRunning: {name}")
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            failed += 1
            print(f"  [FAIL]: {exc}")

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed:
        raise SystemExit(1)
    print("All tests passed!")
