"""End-to-end test for embedding generation, FAISS indexing, and retrieval."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.ai.llm import GeminiConfigurationError
from app.ai.vector_store import load_vector_store, repository_store_path, similarity_search
from app.config import get_settings
from app.services.clone_service import CloneError, CloneService
from app.services.embedding_service import EmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

REPO_URL = "https://github.com/psf/requests"
TEST_QUERIES = [
    "How are HTTP requests sent?",
    "What authentication mechanisms are supported?",
    "How are sessions implemented?",
]


def _print_index_summary(index_result) -> None:
    print("\n=== Index Summary ===")
    print(f"Repository:      {index_result.repository_name}")
    print(f"Documents:       {index_result.total_documents}")
    print(f"Chunks indexed:  {index_result.total_chunks}")
    print(f"Vector count:    {index_result.total_vectors}")
    print(f"Vector store:    {index_result.vector_store_path}")


def _print_search_results(query: str, results) -> None:
    print(f"\n--- Query: {query} ---")
    if not results:
        print("No results returned.")
        return

    source_files = sorted({result.file_path for result in results if result.file_path})
    print(f"Results: {len(results)}")
    print("Source files returned:")
    for file_path in source_files:
        print(f"  - {file_path}")

    for index, result in enumerate(results, start=1):
        preview = result.content.replace("\n", " ").strip()
        if len(preview) > 160:
            preview = preview[:157] + "..."
        print(
            f"  [{index}] score={result.score:.4f} "
            f"file={result.file_path} chunk={result.chunk_id}"
        )
        print(f"      {preview}")


def main() -> int:
    settings = get_settings()

    try:
        if not settings.gemini_api_key:
            raise GeminiConfigurationError("GEMINI_API_KEY is not set")
    except GeminiConfigurationError as exc:
        print(f"Configuration error: {exc}")
        print("Copy .env.example to .env and set GEMINI_API_KEY before running this test.")
        return 1

    clone_service = CloneService(settings)
    embedding_service = EmbeddingService(settings)

    print(f"Testing embeddings pipeline on {REPO_URL}")

    try:
        clone_result = clone_service.clone(REPO_URL)
    except CloneError as exc:
        print(f"Clone failed: {exc}")
        return 1

    repository_name = clone_result.repository_name
    print(f"Repository cloned: {repository_name}")
    print(f"Local path:        {clone_result.local_path}")

    try:
        index_result = embedding_service.index_repository(clone_result.local_path, repository_name)
    except Exception as exc:
        print(f"Indexing failed: {exc}")
        return 1

    _print_index_summary(index_result)

    store_path = repository_store_path(settings.vector_store_dir, repository_name)
    try:
        vectorstore = load_vector_store(store_path, embedding_service.embedding_provider.embeddings)
    except Exception as exc:
        print(f"Failed to load vector store: {exc}")
        return 1

    print("\nVector store load: OK")

    for query in TEST_QUERIES:
        try:
            results = embedding_service.search_repository(repository_name, query, k=5)
        except Exception as exc:
            print(f"Search failed for query '{query}': {exc}")
            return 1

        _print_search_results(query, results)

        if not results:
            print(f"Error: expected retrieval results for query '{query}'")
            return 1

        raw_results = similarity_search(vectorstore, query, k=1)
        if not raw_results:
            print(f"Error: direct similarity search returned no results for '{query}'")
            return 1

    print("\nAll embedding and retrieval tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
