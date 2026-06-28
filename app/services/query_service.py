"""Query service — RAG pipeline orchestration.

This module provides the orchestration layer that connects the Retriever and
Gemini LLM into a complete Retrieval-Augmented Generation pipeline.

Workflow:
    1. Validate the user question.
    2. Retrieve the top-k relevant documents from the FAISS vector store.
    3. Pass those documents as context to the Gemini LLM.
    4. Return the generated answer.

This service contains **no retrieval logic** and **no LLM logic** — it only
coordinates existing services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from langchain_core.documents import Document

from app.ai.llm import GeminiLLM, LLMServiceError
from app.config import Settings, get_settings
from app.services.retriever import RetrieverError, RetrieverService

logger = logging.getLogger(__name__)

DEFAULT_K = 5


class QueryServiceError(Exception):
    """Raised when a query pipeline operation fails."""


@dataclass
class QueryResult:
    """Result of a RAG query, containing the answer and supporting context.

    Attributes:
        answer: The generated answer from the LLM.
        context_documents: The retrieved documents used as context.
        question: The original user question.
        num_documents_retrieved: Number of documents retrieved from the store.
    """

    answer: str
    question: str
    context_documents: list[Document] = field(default_factory=list)
    num_documents_retrieved: int = 0


class QueryService:
    """Orchestrates the RAG pipeline: retrieval → context → LLM → answer.

    This service is the single entry point for answering user questions about
    a repository. It delegates retrieval to ``RetrieverService`` and answer
    generation to ``GeminiLLM``, keeping orchestration logic in one place.

    Example::

        service = QueryService.for_repository("owner/repo")
        result = service.answer("How does authentication work?")
        print(result.answer)
    """

    def __init__(
        self,
        retriever: RetrieverService,
        llm: GeminiLLM,
        *,
        default_k: int = DEFAULT_K,
    ) -> None:
        """Initialise the query service with pre-built components.

        Args:
            retriever: A loaded ``RetrieverService`` instance.
            llm: A configured ``GeminiLLM`` instance.
            default_k: Default number of documents to retrieve per query.
        """
        self._retriever = retriever
        self._llm = llm
        self._default_k = default_k

    # -- Factory constructors ------------------------------------------------

    @classmethod
    def for_repository(
        cls,
        repository_name: str,
        settings: Settings | None = None,
        *,
        default_k: int = DEFAULT_K,
    ) -> QueryService:
        """Create a query service for a previously indexed repository.

        Args:
            repository_name: Repository identifier in ``owner/name`` format.
            settings: Optional application settings; defaults to global settings.
            default_k: Default number of documents to retrieve per query.

        Returns:
            A ready-to-use ``QueryService``.

        Raises:
            QueryServiceError: If the retriever or LLM cannot be initialised.
        """
        settings = settings or get_settings()

        try:
            retriever = RetrieverService.from_repository(repository_name, settings)
        except RetrieverError as exc:
            raise QueryServiceError(
                f"Failed to load retriever for '{repository_name}': {exc}"
            ) from exc

        try:
            llm = GeminiLLM(settings)
        except LLMServiceError as exc:
            raise QueryServiceError(
                f"Failed to initialise LLM: {exc}"
            ) from exc

        logger.info("QueryService ready for repository '%s'", repository_name)
        return cls(retriever, llm, default_k=default_k)

    @classmethod
    def from_path(
        cls,
        store_path: str,
        settings: Settings | None = None,
        *,
        default_k: int = DEFAULT_K,
    ) -> QueryService:
        """Create a query service from an explicit vector store directory.

        Args:
            store_path: Path to the FAISS vector store directory.
            settings: Optional application settings; defaults to global settings.
            default_k: Default number of documents to retrieve per query.

        Returns:
            A ready-to-use ``QueryService``.

        Raises:
            QueryServiceError: If the retriever or LLM cannot be initialised.
        """
        settings = settings or get_settings()

        try:
            retriever = RetrieverService.from_path(store_path, settings)
        except RetrieverError as exc:
            raise QueryServiceError(
                f"Failed to load retriever from '{store_path}': {exc}"
            ) from exc

        try:
            llm = GeminiLLM(settings)
        except LLMServiceError as exc:
            raise QueryServiceError(
                f"Failed to initialise LLM: {exc}"
            ) from exc

        logger.info("QueryService ready from path: %s", store_path)
        return cls(retriever, llm, default_k=default_k)

    # -- Public API ----------------------------------------------------------

    def answer(self, question: str, *, k: int | None = None) -> str:
        """Answer a question using the RAG pipeline.

        This is the simplest entry point — returns just the answer string.

        Args:
            question: The user's natural-language question.
            k: Number of documents to retrieve. Defaults to ``default_k``.

        Returns:
            The generated answer.

        Raises:
            QueryServiceError: If the question is invalid, retrieval fails,
                or the LLM fails.
        """
        result = self.answer_with_context(question, k=k)
        return result.answer

    def answer_with_context(
        self, question: str, *, k: int | None = None
    ) -> QueryResult:
        """Answer a question and return the full result with retrieved context.

        Args:
            question: The user's natural-language question.
            k: Number of documents to retrieve. Defaults to ``default_k``.

        Returns:
            A ``QueryResult`` containing the answer, context documents,
            and metadata.

        Raises:
            QueryServiceError: If the question is invalid, retrieval fails,
                or the LLM fails.
        """
        _validate_question(question)
        k = k or self._default_k

        logger.info("Processing query (k=%d): %s", k, question[:80])

        # Step 1: Retrieve relevant documents
        context_docs = self._retrieve(question, k)

        # Step 2: Generate answer from context
        answer = self._generate(question, context_docs)

        result = QueryResult(
            answer=answer,
            question=question,
            context_documents=context_docs,
            num_documents_retrieved=len(context_docs),
        )

        logger.info(
            "Query complete: %d doc(s) retrieved, answer length=%d",
            result.num_documents_retrieved,
            len(result.answer),
        )
        return result

    # -- Internal pipeline steps ---------------------------------------------

    def _retrieve(self, question: str, k: int) -> list[Document]:
        """Retrieve documents from the vector store."""
        try:
            documents = self._retriever.search(question, k=k)
        except RetrieverError as exc:
            logger.error("Retrieval failed: %s", exc)
            raise QueryServiceError(f"Retrieval failed: {exc}") from exc
        except Exception as exc:
            logger.error("Unexpected retrieval error: %s", exc)
            raise QueryServiceError(
                f"Unexpected error during retrieval: {exc}"
            ) from exc

        logger.info("Retrieved %d document(s)", len(documents))
        return documents

    def _generate(self, question: str, context: list[Document]) -> str:
        """Generate an answer from the LLM."""
        try:
            answer = self._llm.generate_answer(question, context)
        except LLMServiceError as exc:
            logger.error("LLM generation failed: %s", exc)
            raise QueryServiceError(f"LLM generation failed: {exc}") from exc
        except Exception as exc:
            logger.error("Unexpected LLM error: %s", exc)
            raise QueryServiceError(
                f"Unexpected error during LLM generation: {exc}"
            ) from exc

        return answer


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _validate_question(question: str) -> None:
    """Raise QueryServiceError if the question is empty or whitespace-only."""
    if not question or not question.strip():
        raise QueryServiceError("Question must not be empty")
