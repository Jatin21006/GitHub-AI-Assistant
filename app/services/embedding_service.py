"""Embedding generation and vector indexing service."""

from __future__ import annotations

import logging
from pathlib import Path

from app.ai.llm import GeminiEmbeddingProvider
from app.ai.vector_store import (
    build_vector_store,
    load_vector_store,
    repository_store_path,
    save_vector_store,
    similarity_search,
)
from app.config import Settings, get_settings
from app.models.schemas import IndexResult, RetrievalResult
from app.services.parser_service import parse_repository

logger = logging.getLogger(__name__)


class EmbeddingServiceError(Exception):
    """Raised when indexing or retrieval fails."""


class EmbeddingService:
    """Orchestrate repository parsing, embedding, and FAISS indexing."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._embedding_provider = GeminiEmbeddingProvider(self._settings)

    @property
    def embedding_provider(self) -> GeminiEmbeddingProvider:
        """Public access to the Gemini embedding provider."""
        return self._embedding_provider

    def index_repository(self, repo_path: Path, repository_name: str) -> IndexResult:
        """
        Index a cloned repository end-to-end.

        Pipeline:
            Repository -> Documents -> Chunks -> Gemini Embeddings -> FAISS Index
        """
        repo_path = repo_path.resolve()
        if not repo_path.is_dir():
            raise EmbeddingServiceError(f"Repository path does not exist: {repo_path}")

        logger.info("Starting indexing for '%s' at %s", repository_name, repo_path)

        chunks, stats = parse_repository(repo_path, repository_name)
        if not chunks:
            raise EmbeddingServiceError(
                f"No indexable chunks found for repository '{repository_name}'."
            )

        vectorstore = build_vector_store(chunks, self._embedding_provider)
        store_path = repository_store_path(self._settings.vector_store_dir, repository_name)
        save_vector_store(vectorstore, store_path)

        result = IndexResult(
            repository_name=repository_name,
            total_documents=stats.total_documents,
            total_chunks=stats.total_chunks,
            total_vectors=len(chunks),
            vector_store_path=str(store_path),
        )

        logger.info(
            "Indexed '%s': documents=%d chunks=%d vectors=%d path=%s",
            repository_name,
            result.total_documents,
            result.total_chunks,
            result.total_vectors,
            result.vector_store_path,
        )
        return result

    def search_repository(
        self,
        repository_name: str,
        query: str,
        k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve the most relevant chunks for a query from a repository index.

        Returns:
            Retrieved chunks with similarity scores and source file metadata.
        """
        if not query.strip():
            raise EmbeddingServiceError("Query must not be empty")

        store_path = repository_store_path(self._settings.vector_store_dir, repository_name)
        if not store_path.exists():
            raise EmbeddingServiceError(
                f"No vector store found for repository '{repository_name}' at {store_path}. "
                "Run index_repository() first."
            )

        logger.info("Searching '%s' for query: %s", repository_name, query)
        vectorstore = load_vector_store(store_path, self._embedding_provider.embeddings)
        results = similarity_search(vectorstore, query, k=k)

        retrieval_results: list[RetrievalResult] = []
        for document, score in results:
            metadata = dict(document.metadata)
            retrieval_results.append(
                RetrievalResult(
                    chunk_id=str(metadata.get("chunk_id", "")),
                    content=document.page_content,
                    score=float(score),
                    metadata=metadata,
                    file_path=str(metadata.get("file_path", "")),
                    file_name=str(metadata.get("file_name", "")),
                    language=str(metadata.get("language", "")),
                    extension=str(metadata.get("extension", "")),
                )
            )

        logger.info(
            "Retrieved %d chunk(s) for '%s' from %d unique file(s)",
            len(retrieval_results),
            repository_name,
            len({result.file_path for result in retrieval_results if result.file_path}),
        )
        return retrieval_results


def index_repository(repo_path: Path, repository_name: str, settings: Settings | None = None) -> IndexResult:
    """Convenience wrapper for EmbeddingService.index_repository()."""
    return EmbeddingService(settings).index_repository(repo_path, repository_name)


def search_repository(
    repository_name: str,
    query: str,
    k: int = 5,
    settings: Settings | None = None,
) -> list[RetrievalResult]:
    """Convenience wrapper for EmbeddingService.search_repository()."""
    return EmbeddingService(settings).search_repository(repository_name, query, k=k)
