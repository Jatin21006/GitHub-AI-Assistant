"""Retriever service for querying FAISS vector stores.

This module provides a retrieval layer that loads an existing FAISS vector
store and returns the most relevant code/document chunks for a user query.

It performs retrieval only — no LLM calls or answer generation.
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.ai.llm import GeminiEmbeddingProvider
from app.ai.vector_store import (
    load_vector_store as _load_faiss_index,
    repository_store_path,
    similarity_search as _similarity_search,
)
from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

DEFAULT_K = 5


class RetrieverError(Exception):
    """Raised when a retrieval operation fails."""


# ---------------------------------------------------------------------------
# RetrieverService (stateful, reusable)
# ---------------------------------------------------------------------------


class RetrieverService:
    """Stateful retriever that loads a vector store once and supports repeated queries.

    Designed to be instantiated once per repository and reused across multiple
    queries, avoiding redundant FAISS loads and embedding model initialisation.

    Example::

        service = RetrieverService.from_repository("owner/repo")
        results = service.search("How does authentication work?", k=3)
    """

    def __init__(
        self,
        vector_store: FAISS,
        *,
        store_path: Path | None = None,
    ) -> None:
        """Initialise with an already-loaded FAISS vector store.

        Args:
            vector_store: A loaded FAISS vector store instance.
            store_path: Optional path the store was loaded from (for logging).
        """
        self._vector_store = vector_store
        self._store_path = store_path

    # -- Factory constructors ------------------------------------------------

    @classmethod
    def from_repository(
        cls,
        repository_name: str,
        settings: Settings | None = None,
    ) -> RetrieverService:
        """Create a retriever for a previously indexed repository.

        Args:
            repository_name: Repository identifier in ``owner/name`` format.
            settings: Optional application settings; defaults to global settings.

        Returns:
            A ``RetrieverService`` backed by the repository's FAISS index.

        Raises:
            RetrieverError: If no index exists for the given repository.
        """
        settings = settings or get_settings()
        store_path = repository_store_path(settings.vector_store_dir, repository_name)
        vector_store = _load_store(store_path, settings)
        logger.info("Retriever ready for repository '%s'", repository_name)
        return cls(vector_store, store_path=store_path)

    @classmethod
    def from_path(
        cls,
        store_path: str | Path,
        settings: Settings | None = None,
    ) -> RetrieverService:
        """Create a retriever from an explicit vector store directory.

        Args:
            store_path: Directory containing a saved FAISS index.
            settings: Optional application settings; defaults to global settings.

        Returns:
            A ``RetrieverService`` backed by the FAISS index at *store_path*.

        Raises:
            RetrieverError: If the directory or index file does not exist.
        """
        store_path = Path(store_path)
        settings = settings or get_settings()
        vector_store = _load_store(store_path, settings)
        logger.info("Retriever ready from path: %s", store_path)
        return cls(vector_store, store_path=store_path)

    # -- Public query methods ------------------------------------------------

    def search(self, query: str, k: int = DEFAULT_K) -> list[Document]:
        """Return the top-*k* most relevant documents for *query*.

        Args:
            query: Natural-language search query.
            k: Number of results to return. Must be a positive integer.

        Returns:
            List of ``Document`` objects ordered by relevance (most relevant first).

        Raises:
            RetrieverError: If the query is empty or *k* is invalid.
        """
        _validate_query(query)
        _validate_k(k)

        logger.info("Searching for query (k=%d): %s", k, query[:80])
        results = self._vector_store.similarity_search(query, k=k)
        logger.info("Search returned %d result(s)", len(results))
        return results

    def search_with_scores(
        self, query: str, k: int = DEFAULT_K
    ) -> list[tuple[Document, float]]:
        """Return the top-*k* most relevant documents with similarity scores.

        Args:
            query: Natural-language search query.
            k: Number of results to return. Must be a positive integer.

        Returns:
            List of ``(Document, score)`` tuples ordered by relevance.
            Lower scores indicate higher similarity for L2-based FAISS indexes.

        Raises:
            RetrieverError: If the query is empty or *k* is invalid.
        """
        _validate_query(query)
        _validate_k(k)

        logger.info("Searching with scores for query (k=%d): %s", k, query[:80])
        results = _similarity_search(self._vector_store, query, k=k)
        logger.info("Search returned %d scored result(s)", len(results))
        return results

    @property
    def vector_store(self) -> FAISS:
        """Direct access to the underlying FAISS vector store."""
        return self._vector_store


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def load_retriever(
    store_path: str | Path,
    settings: Settings | None = None,
) -> RetrieverService:
    """Load a FAISS vector store and return a ready-to-query ``RetrieverService``.

    This is a convenience wrapper around ``RetrieverService.from_path``.

    Args:
        store_path: Directory containing a saved FAISS index.
        settings: Optional application settings; defaults to global settings.

    Returns:
        A ``RetrieverService`` instance.

    Raises:
        RetrieverError: If the store path is invalid or the index cannot be loaded.
    """
    return RetrieverService.from_path(store_path, settings)


def retrieve(
    store_path: str | Path,
    query: str,
    k: int = DEFAULT_K,
    settings: Settings | None = None,
) -> list[Document]:
    """One-shot retrieval: load the vector store and return top-*k* documents.

    Args:
        store_path: Directory containing a saved FAISS index.
        query: Natural-language search query.
        k: Number of results to return.
        settings: Optional application settings.

    Returns:
        List of ``Document`` objects ordered by relevance.

    Raises:
        RetrieverError: If the store cannot be loaded or the query is invalid.
    """
    retriever = load_retriever(store_path, settings)
    return retriever.search(query, k=k)


def retrieve_with_scores(
    store_path: str | Path,
    query: str,
    k: int = DEFAULT_K,
    settings: Settings | None = None,
) -> list[tuple[Document, float]]:
    """One-shot retrieval with scores: load the vector store and return top-*k* results.

    Args:
        store_path: Directory containing a saved FAISS index.
        query: Natural-language search query.
        k: Number of results to return.
        settings: Optional application settings.

    Returns:
        List of ``(Document, score)`` tuples ordered by relevance.

    Raises:
        RetrieverError: If the store cannot be loaded or the query is invalid.
    """
    retriever = load_retriever(store_path, settings)
    return retriever.search_with_scores(query, k=k)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_store(store_path: Path, settings: Settings) -> FAISS:
    """Load a FAISS vector store with full error handling."""
    if not store_path.is_dir():
        raise RetrieverError(
            f"Vector store directory not found: {store_path}. "
            "Ensure the repository has been indexed first."
        )

    index_file = store_path / "index.faiss"
    if not index_file.exists():
        raise RetrieverError(
            f"FAISS index file not found at {index_file}. "
            "The directory exists but does not contain a valid FAISS index."
        )

    try:
        embedding_provider = GeminiEmbeddingProvider(settings)
        vector_store = _load_faiss_index(store_path, embedding_provider.embeddings)
    except FileNotFoundError as exc:
        raise RetrieverError(f"Failed to load vector store from {store_path}: {exc}") from exc
    except Exception as exc:
        logger.error("Unexpected error loading vector store from %s: %s", store_path, exc)
        raise RetrieverError(
            f"Failed to load vector store from {store_path}: {exc}"
        ) from exc

    logger.info("Loaded vector store from %s", store_path)
    return vector_store


def _validate_query(query: str) -> None:
    """Raise RetrieverError if the query is empty or whitespace-only."""
    if not query or not query.strip():
        raise RetrieverError("Query must not be empty")


def _validate_k(k: int) -> None:
    """Raise RetrieverError if k is not a positive integer."""
    if not isinstance(k, int) or k <= 0:
        raise RetrieverError(f"k must be a positive integer, got {k!r}")
