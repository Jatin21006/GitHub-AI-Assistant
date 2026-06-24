"""FAISS vector store management."""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.ai.llm import GeminiEmbeddingProvider

logger = logging.getLogger(__name__)

INDEX_FILENAME = "index"


def repository_store_path(base_dir: Path, repository_name: str) -> Path:
    """Build a filesystem-safe vector store path for a repository."""
    safe_name = repository_name.replace("/", "_")
    return base_dir / safe_name


def build_vector_store(
    chunks: list[Document],
    embedding_provider: GeminiEmbeddingProvider,
) -> FAISS:
    """
    Build a FAISS index from document chunks and Gemini embeddings.

    Embeddings are generated in batches; all chunk metadata is preserved.
    """
    if not chunks:
        raise ValueError("Cannot build a vector store from an empty chunk list")

    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]

    logger.info("Building FAISS index for %d chunk(s)", len(chunks))
    vectors = embedding_provider.embed_documents(texts)
    text_embeddings = list(zip(texts, vectors, strict=True))

    vectorstore = FAISS.from_embeddings(
        text_embeddings=text_embeddings,
        embedding=embedding_provider.embeddings,
        metadatas=metadatas,
    )

    logger.info("FAISS index built with %d vector(s)", len(chunks))
    return vectorstore


def save_vector_store(vectorstore: FAISS, store_path: Path) -> Path:
    """Persist a FAISS index to disk."""
    store_path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(store_path), index_name=INDEX_FILENAME)
    logger.info("Saved FAISS index to %s", store_path)
    return store_path


def load_vector_store(store_path: Path, embeddings: Embeddings) -> FAISS:
    """Load a persisted FAISS index from disk."""
    if not store_path.is_dir():
        raise FileNotFoundError(f"Vector store directory not found: {store_path}")

    index_file = store_path / f"{INDEX_FILENAME}.faiss"
    if not index_file.exists():
        raise FileNotFoundError(f"FAISS index file not found: {index_file}")

    logger.info("Loading FAISS index from %s", store_path)
    vectorstore = FAISS.load_local(
        str(store_path),
        embeddings,
        index_name=INDEX_FILENAME,
        allow_dangerous_deserialization=True,
    )
    logger.info("FAISS index loaded from %s", store_path)
    return vectorstore


def similarity_search(
    vectorstore: FAISS,
    query: str,
    k: int = 5,
) -> list[tuple[Document, float]]:
    """
    Search the vector store for chunks similar to the query.

    Returns:
        List of (Document, score) tuples ordered by relevance.
    """
    if k <= 0:
        raise ValueError("k must be a positive integer")

    logger.info("Running similarity search (k=%d)", k)
    results = vectorstore.similarity_search_with_score(query, k=k)
    logger.info("Similarity search returned %d result(s)", len(results))
    return results
