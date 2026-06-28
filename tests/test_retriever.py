"""Comprehensive test suite for app.services.retriever module."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.services.retriever import (
    DEFAULT_K,
    RetrieverError,
    RetrieverService,
    load_retriever,
    retrieve,
    retrieve_with_scores,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

FAKE_EMBEDDING_DIM = 8


class FakeEmbeddings(Embeddings):
    """Deterministic fake embeddings for testing (no network calls)."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[float(i + 1)] * FAKE_EMBEDDING_DIM for i, _ in enumerate(texts)]

    def embed_query(self, text: str) -> list[float]:
        return [1.0] * FAKE_EMBEDDING_DIM


def _sample_documents() -> list[Document]:
    """Return sample LangChain Documents for testing."""
    return [
        Document(
            page_content="def authenticate(user, password): return check_credentials(user, password)",
            metadata={
                "file_path": "src/auth.py",
                "file_type": "python",
                "file_name": "auth.py",
                "language": "python",
                "extension": ".py",
                "chunk_id": "src/auth.py:0",
            },
        ),
        Document(
            page_content="class UserRepository: def find_by_id(self, user_id): return self.db.query(user_id)",
            metadata={
                "file_path": "src/repository.py",
                "file_type": "python",
                "file_name": "repository.py",
                "language": "python",
                "extension": ".py",
                "chunk_id": "src/repository.py:0",
            },
        ),
        Document(
            page_content="# API Documentation\n\nThis module exposes REST endpoints for user management.",
            metadata={
                "file_path": "docs/api.md",
                "file_type": "markdown",
                "file_name": "api.md",
                "language": "markdown",
                "extension": ".md",
                "chunk_id": "docs/api.md:0",
            },
        ),
        Document(
            page_content="function handleLogin(event) { event.preventDefault(); fetch('/api/login'); }",
            metadata={
                "file_path": "static/app.js",
                "file_type": "javascript",
                "file_name": "app.js",
                "language": "javascript",
                "extension": ".js",
                "chunk_id": "static/app.js:0",
            },
        ),
    ]


def _build_test_faiss(documents: list[Document] | None = None) -> FAISS:
    """Build a FAISS index from sample documents with fake embeddings."""
    docs = documents or _sample_documents()
    embeddings = FakeEmbeddings()
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]
    return FAISS.from_texts(texts=texts, embedding=embeddings, metadatas=metadatas)


def _save_test_faiss(tmp_dir: Path, documents: list[Document] | None = None) -> Path:
    """Build and save a FAISS index to a temp directory, return the path."""
    faiss_store = _build_test_faiss(documents)
    faiss_store.save_local(str(tmp_dir), index_name="index")
    return tmp_dir


def _mock_embedding_provider() -> MagicMock:
    """Create a mock GeminiEmbeddingProvider that returns FakeEmbeddings."""
    mock_provider = MagicMock()
    mock_provider.embeddings = FakeEmbeddings()
    return mock_provider


# ---------------------------------------------------------------------------
# RetrieverService tests
# ---------------------------------------------------------------------------


def test_retriever_service_from_vector_store() -> None:
    """RetrieverService can be created from a FAISS vector store."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)
    assert service.vector_store is faiss_store
    print("  [PASS] RetrieverService created from vector store")


def test_retriever_service_search() -> None:
    """search() returns the correct number of Document objects."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)
    results = service.search("authentication", k=2)
    assert isinstance(results, list)
    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    print(f"  [PASS] search() returned {len(results)} documents")


def test_retriever_service_search_with_scores() -> None:
    """search_with_scores() returns (Document, float) tuples."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)
    results = service.search_with_scores("user repository", k=3)
    assert isinstance(results, list)
    assert len(results) == 3
    for doc, score in results:
        assert isinstance(doc, Document)
        assert float(score) == float(score), f"Score is not numeric: {type(score)}"
    print(f"  [PASS] search_with_scores() returned {len(results)} scored results")


def test_retriever_service_default_k() -> None:
    """search() uses DEFAULT_K when k is not specified."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)
    results = service.search("test query")
    # With 4 documents, min(DEFAULT_K, 4) results expected
    assert len(results) == min(DEFAULT_K, 4)
    print(f"  [PASS] Default k returned {len(results)} results")


def test_retriever_service_configurable_k() -> None:
    """search() respects custom k values."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)

    for k in [1, 2, 3, 4]:
        results = service.search("query", k=k)
        assert len(results) == k, f"Expected {k} results, got {len(results)}"

    print("  [PASS] k=1,2,3,4 all returned correct counts")


def test_retriever_service_preserves_metadata() -> None:
    """Retrieved documents retain their original metadata."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)
    results = service.search("authenticate", k=1)
    assert len(results) == 1
    meta = results[0].metadata
    assert "file_path" in meta
    assert "file_type" in meta
    assert "chunk_id" in meta
    print(f"  [PASS] Metadata preserved: file_path={meta['file_path']}")


def test_retriever_service_search_empty_query_raises() -> None:
    """search() raises RetrieverError for empty query."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)
    try:
        service.search("")
        assert False, "Should have raised RetrieverError"
    except RetrieverError:
        pass
    try:
        service.search("   ")
        assert False, "Should have raised RetrieverError for whitespace"
    except RetrieverError:
        pass
    print("  [PASS] Empty and whitespace queries raise RetrieverError")


def test_retriever_service_search_invalid_k_raises() -> None:
    """search() raises RetrieverError for invalid k values."""
    faiss_store = _build_test_faiss()
    service = RetrieverService(faiss_store)
    for invalid_k in [0, -1, -100]:
        try:
            service.search("query", k=invalid_k)
            assert False, f"Should have raised RetrieverError for k={invalid_k}"
        except RetrieverError:
            pass
    print("  [PASS] Invalid k values (0, -1, -100) raise RetrieverError")


def test_retriever_service_from_path() -> None:
    """RetrieverService.from_path() loads a saved vector store."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        _save_test_faiss(tmp_dir)
        with patch("app.services.retriever.GeminiEmbeddingProvider") as mock_cls:
            mock_cls.return_value = _mock_embedding_provider()

            service = RetrieverService.from_path(tmp_dir)
            assert service.vector_store is not None
            results = service.search("test", k=2)
            assert len(results) == 2
        print(f"  [PASS] from_path() loaded store and returned {len(results)} results")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_retriever_service_from_repository() -> None:
    """RetrieverService.from_repository() resolves the store path and loads."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        store_dir = tmp_dir / "owner_repo"
        store_dir.mkdir()
        _save_test_faiss(store_dir)

        with patch("app.services.retriever.GeminiEmbeddingProvider") as mock_cls:
            mock_cls.return_value = _mock_embedding_provider()

            with patch("app.services.retriever.get_settings") as mock_settings:
                settings = MagicMock()
                settings.vector_store_dir = tmp_dir
                mock_settings.return_value = settings

                service = RetrieverService.from_repository("owner/repo")
                results = service.search("test", k=1)
                assert len(results) == 1
        print("  [PASS] from_repository() resolved path and loaded store")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


def test_missing_directory_raises() -> None:
    """RetrieverService.from_path() raises RetrieverError for missing directory."""
    try:
        RetrieverService.from_path("/non/existent/path")
        assert False, "Should have raised RetrieverError"
    except RetrieverError as exc:
        assert "not found" in str(exc).lower()
    print("  [PASS] Missing directory raises RetrieverError")


def test_empty_directory_raises() -> None:
    """RetrieverService.from_path() raises RetrieverError for dir without index."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        try:
            RetrieverService.from_path(tmp_dir)
            assert False, "Should have raised RetrieverError"
        except RetrieverError as exc:
            assert "index" in str(exc).lower()
        print("  [PASS] Empty directory (no index.faiss) raises RetrieverError")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_load_retriever_missing_path_raises() -> None:
    """load_retriever() raises RetrieverError for missing path."""
    try:
        load_retriever("/does/not/exist")
        assert False, "Should have raised RetrieverError"
    except RetrieverError:
        pass
    print("  [PASS] load_retriever() with missing path raises RetrieverError")


# ---------------------------------------------------------------------------
# Module-level convenience function tests
# ---------------------------------------------------------------------------


def test_load_retriever_function() -> None:
    """load_retriever() returns a working RetrieverService."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        _save_test_faiss(tmp_dir)
        with patch("app.services.retriever.GeminiEmbeddingProvider") as mock_cls:
            mock_cls.return_value = _mock_embedding_provider()

            service = load_retriever(tmp_dir)
            assert isinstance(service, RetrieverService)
        print("  [PASS] load_retriever() returned RetrieverService")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_retrieve_function() -> None:
    """retrieve() performs one-shot retrieval and returns documents."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        _save_test_faiss(tmp_dir)
        with patch("app.services.retriever.GeminiEmbeddingProvider") as mock_cls:
            mock_cls.return_value = _mock_embedding_provider()

            results = retrieve(tmp_dir, "authentication", k=2)
            assert len(results) == 2
            assert all(isinstance(doc, Document) for doc in results)
        print(f"  [PASS] retrieve() returned {len(results)} documents")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_retrieve_with_scores_function() -> None:
    """retrieve_with_scores() performs one-shot retrieval with scores."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        _save_test_faiss(tmp_dir)
        with patch("app.services.retriever.GeminiEmbeddingProvider") as mock_cls:
            mock_cls.return_value = _mock_embedding_provider()

            results = retrieve_with_scores(tmp_dir, "user repository", k=3)
            assert len(results) == 3
            for doc, score in results:
                assert isinstance(doc, Document)
                assert float(score) == float(score), f"Score is not numeric: {type(score)}"
        print(f"  [PASS] retrieve_with_scores() returned {len(results)} scored results")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        # RetrieverService core
        ("RetrieverService from vector store", test_retriever_service_from_vector_store),
        ("RetrieverService search", test_retriever_service_search),
        ("RetrieverService search with scores", test_retriever_service_search_with_scores),
        ("RetrieverService default k", test_retriever_service_default_k),
        ("RetrieverService configurable k", test_retriever_service_configurable_k),
        ("RetrieverService preserves metadata", test_retriever_service_preserves_metadata),
        ("RetrieverService empty query raises", test_retriever_service_search_empty_query_raises),
        ("RetrieverService invalid k raises", test_retriever_service_search_invalid_k_raises),
        # Factory constructors
        ("RetrieverService.from_path", test_retriever_service_from_path),
        ("RetrieverService.from_repository", test_retriever_service_from_repository),
        # Error handling
        ("Missing directory raises", test_missing_directory_raises),
        ("Empty directory raises", test_empty_directory_raises),
        ("load_retriever missing path raises", test_load_retriever_missing_path_raises),
        # Convenience functions
        ("load_retriever function", test_load_retriever_function),
        ("retrieve function", test_retrieve_function),
        ("retrieve_with_scores function", test_retrieve_with_scores_function),
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

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed:
        raise SystemExit(1)
    print("All tests passed!")
