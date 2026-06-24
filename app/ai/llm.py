"""LangChain integrations for Google Gemini LLM and embeddings."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import lru_cache

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class GeminiConfigurationError(Exception):
    """Raised when Gemini credentials or configuration are missing."""


@dataclass
class EmbeddingStats:
    """Statistics collected while generating embeddings."""

    total_texts: int = 0
    total_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    total_retries: int = 0
    total_vectors: int = 0


def _require_api_key(settings: Settings) -> str:
    if not settings.gemini_api_key:
        raise GeminiConfigurationError(
            "GEMINI_API_KEY is not set. Add it to your .env file before using Gemini."
        )
    return settings.gemini_api_key


@lru_cache
def get_llm() -> ChatGoogleGenerativeAI:
    """Return a cached Gemini chat model instance."""
    return _create_llm(get_settings())


@lru_cache
def get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    """Return a cached Gemini embeddings model instance."""
    return _create_embeddings_model(get_settings())


def _create_llm(settings: Settings) -> ChatGoogleGenerativeAI:
    api_key = _require_api_key(settings)

    logger.info("Initializing Gemini LLM model: %s", settings.llm_model)
    return ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=api_key,
        temperature=0.2,
    )


def _create_embeddings_model(settings: Settings) -> GoogleGenerativeAIEmbeddings:
    api_key = _require_api_key(settings)

    logger.info("Initializing Gemini embedding model: %s", settings.embedding_model)
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=api_key,
    )


class GeminiEmbeddingProvider:
    """Reusable Gemini embedding provider with batching, retries, and stats."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        _require_api_key(self._settings)
        self._embeddings = _create_embeddings_model(self._settings)
        self.stats = EmbeddingStats()

    @property
    def embeddings(self) -> GoogleGenerativeAIEmbeddings:
        """Underlying LangChain embeddings instance for FAISS compatibility."""
        return self._embeddings

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts in batches with retry handling."""
        if not texts:
            return []

        batch_size = max(1, self._settings.embedding_batch_size)
        max_retries = max(1, self._settings.embedding_max_retries)
        all_vectors: list[list[float]] = []

        self.stats.total_texts = len(texts)
        logger.info("Embedding %d text(s) in batches of %d", len(texts), batch_size)

        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            batch_number = (start // batch_size) + 1
            self.stats.total_batches += 1

            vectors = self._embed_batch_with_retry(batch, batch_number, max_retries)
            all_vectors.extend(vectors)
            self.stats.successful_batches += 1
            self.stats.total_vectors += len(vectors)

        logger.info(
            "Embedding complete: texts=%d batches=%d retries=%d vectors=%d",
            self.stats.total_texts,
            self.stats.total_batches,
            self.stats.total_retries,
            self.stats.total_vectors,
        )
        return all_vectors

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string with retry handling."""
        max_retries = max(1, self._settings.embedding_max_retries)

        for attempt in range(1, max_retries + 1):
            try:
                return self._embeddings.embed_query(text)
            except Exception as exc:
                if attempt >= max_retries:
                    logger.error("Failed to embed query after %d attempts: %s", max_retries, exc)
                    raise

                self.stats.total_retries += 1
                delay = 2 ** (attempt - 1)
                logger.warning(
                    "Query embedding failed (attempt %d/%d): %s. Retrying in %ds",
                    attempt,
                    max_retries,
                    exc,
                    delay,
                )
                time.sleep(delay)

        raise RuntimeError("Unexpected embedding retry loop exit")

    def _embed_batch_with_retry(
        self,
        batch: list[str],
        batch_number: int,
        max_retries: int,
    ) -> list[list[float]]:
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug("Embedding batch %d (%d text(s))", batch_number, len(batch))
                return self._embeddings.embed_documents(batch)
            except Exception as exc:
                if attempt >= max_retries:
                    self.stats.failed_batches += 1
                    logger.error(
                        "Batch %d failed after %d attempts: %s",
                        batch_number,
                        max_retries,
                        exc,
                    )
                    raise

                self.stats.total_retries += 1
                delay = 2 ** (attempt - 1)
                logger.warning(
                    "Batch %d failed (attempt %d/%d): %s. Retrying in %ds",
                    batch_number,
                    attempt,
                    max_retries,
                    exc,
                    delay,
                )
                time.sleep(delay)

        raise RuntimeError("Unexpected batch embedding retry loop exit")
