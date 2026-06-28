"""Vector store service for building, saving, and loading FAISS indexes."""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
INDEX_FILENAME = "index"
DEFAULT_VECTOR_STORE_DIR = "data/vector_store"


class VectorStoreError(Exception):
    """Raised when a vector store operation fails."""


def build_vector_store(
    documents: list[Document],
    settings: Settings | None = None,
) -> FAISS:
    """
    Build a FAISS vector store from LangChain Document objects.

    The documents are split into chunks using RecursiveCharacterTextSplitter,
    embedded via GoogleGenerativeAIEmbeddings, and indexed in a FAISS store.
    Each chunk retains its source metadata (file_path, file_type, chunk_id).

    Args:
        documents: LangChain Document objects, typically from code_parser.py.
        settings: Optional application settings; defaults to global settings.

    Returns:
        A FAISS vector store populated with embedded document chunks.

    Raises:
        VectorStoreError: If the document list is empty or embedding fails.
    """
    if not documents:
        raise VectorStoreError("Cannot build a vector store from an empty document list")

    settings = settings or get_settings()

    # --- 1. Split documents into chunks ---
    chunks = _split_documents(documents)

    # --- 2. Generate embeddings ---
    embeddings = _create_embeddings(settings)

    # --- 3. Build FAISS index ---
    try:
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        logger.info("Building FAISS index from %d chunk(s)", len(chunks))
        vector_store = FAISS.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
        )
        logger.info("FAISS index built successfully with %d vector(s)", len(chunks))
    except Exception as exc:
        logger.error("Failed to build FAISS index: %s", exc)
        raise VectorStoreError(f"Failed to build FAISS index: {exc}") from exc

    return vector_store


def save_vector_store(vector_store: FAISS, path: str | Path | None = None) -> Path:
    """
    Persist a FAISS vector store to disk.

    Args:
        vector_store: The FAISS vector store to save.
        path: Directory to save the index into. Defaults to data/vector_store/.

    Returns:
        The Path where the index was saved.

    Raises:
        VectorStoreError: If saving fails.
    """
    store_path = Path(path) if path is not None else _default_store_path()
    store_path.mkdir(parents=True, exist_ok=True)

    try:
        vector_store.save_local(str(store_path), index_name=INDEX_FILENAME)
        logger.info("Saved FAISS index to %s", store_path)
    except Exception as exc:
        logger.error("Failed to save FAISS index to %s: %s", store_path, exc)
        raise VectorStoreError(f"Failed to save FAISS index to {store_path}: {exc}") from exc

    return store_path


def load_vector_store(
    path: str | Path | None = None,
    settings: Settings | None = None,
) -> FAISS:
    """
    Load a previously saved FAISS vector store from disk.

    Args:
        path: Directory containing the saved index. Defaults to data/vector_store/.
        settings: Optional application settings; defaults to global settings.

    Returns:
        The loaded FAISS vector store.

    Raises:
        VectorStoreError: If the path does not exist or loading fails.
    """
    store_path = Path(path) if path is not None else _default_store_path()

    if not store_path.is_dir():
        raise VectorStoreError(f"Vector store directory not found: {store_path}")

    index_file = store_path / f"{INDEX_FILENAME}.faiss"
    if not index_file.exists():
        raise VectorStoreError(f"FAISS index file not found: {index_file}")

    settings = settings or get_settings()
    embeddings = _create_embeddings(settings)

    try:
        logger.info("Loading FAISS index from %s", store_path)
        vector_store = FAISS.load_local(
            str(store_path),
            embeddings,
            index_name=INDEX_FILENAME,
            allow_dangerous_deserialization=True,
        )
        logger.info("FAISS index loaded successfully from %s", store_path)
    except Exception as exc:
        logger.error("Failed to load FAISS index from %s: %s", store_path, exc)
        raise VectorStoreError(f"Failed to load FAISS index from {store_path}: {exc}") from exc

    return vector_store


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _split_documents(documents: list[Document]) -> list[Document]:
    """
    Split documents into chunks and assign metadata to each chunk.

    Each chunk receives:
        - file_path: inherited from the source document
        - file_type: inherited from the source document (extension/language)
        - chunk_id: unique identifier in the form file_path:index
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    logger.info(
        "Splitting %d document(s) (chunk_size=%d, chunk_overlap=%d)",
        len(documents),
        CHUNK_SIZE,
        CHUNK_OVERLAP,
    )

    chunks: list[Document] = []
    per_file_counter: dict[str, int] = {}

    for document in documents:
        file_path = document.metadata.get("file_path", "unknown")
        file_type = document.metadata.get("file_type", document.metadata.get("language", "unknown"))

        split_chunks = splitter.split_documents([document])

        for chunk in split_chunks:
            index = per_file_counter.get(file_path, 0)
            per_file_counter[file_path] = index + 1

            chunk.metadata["file_path"] = file_path
            chunk.metadata["file_type"] = file_type
            chunk.metadata["chunk_id"] = f"{file_path}:{index}"

            chunks.append(chunk)

    logger.info("Created %d chunk(s) from %d document(s)", len(chunks), len(documents))
    return chunks


def _create_embeddings(settings: Settings) -> GoogleGenerativeAIEmbeddings:
    """Create a GoogleGenerativeAIEmbeddings instance from settings."""
    api_key = settings.gemini_api_key or settings.google_api_key
    if not api_key:
        raise VectorStoreError(
            "GEMINI_API_KEY is not set. Add it to your .env file before using the vector store."
        )

    logger.info("Initializing embedding model: %s", settings.embedding_model)
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=api_key,
    )


def _default_store_path() -> Path:
    """Return the default vector store directory resolved from project root."""
    from app.config import PROJECT_ROOT

    return PROJECT_ROOT / DEFAULT_VECTOR_STORE_DIR
