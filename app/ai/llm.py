"""LangChain integrations for Google Gemini LLM and embeddings."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class GeminiConfigurationError(Exception):
    """Raised when Gemini credentials or configuration are missing."""


class LLMServiceError(Exception):
    """Raised when an LLM operation fails."""


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


# ---------------------------------------------------------------------------
# LLM Service — prompt construction and answer generation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a knowledgeable GitHub repository assistant. Your role is to help \
developers understand codebases by answering questions about repository \
structure, implementation details, and code behavior.

Rules:
1. Answer ONLY using the repository context provided below.
2. If the answer cannot be determined from the provided context, say so \
clearly. Do NOT guess or hallucinate.
3. When referencing code, mention the source file path.
4. Be concise, accurate, and developer-friendly.
5. Use code blocks with appropriate language tags when showing code snippets.
"""

CONTEXT_HEADER = "## Repository Context\n\n"
QUESTION_HEADER = "\n\n## Question\n\n"
NO_CONTEXT_NOTICE = (
    "No repository context was provided. "
    "I cannot answer questions without relevant code or documentation context."
)


class GeminiLLM:
    """Service for generating answers from a user question and repository context.

    This class handles prompt construction and Gemini LLM invocation.
    It does **not** perform retrieval, vector search, or repository parsing.

    Example::

        llm = GeminiLLM()
        answer = llm.generate_answer(
            question="How does authentication work?",
            context=retrieved_documents,
        )
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise the LLM service.

        Args:
            settings: Optional application settings; defaults to global settings.

        Raises:
            LLMServiceError: If the Gemini API key is not configured.
        """
        self._settings = settings or get_settings()
        try:
            self._llm = _create_llm(self._settings)
        except GeminiConfigurationError as exc:
            raise LLMServiceError(str(exc)) from exc

        logger.info("GeminiLLM initialised with model: %s", self._settings.llm_model)

    @property
    def model_name(self) -> str:
        """The configured Gemini model name."""
        return self._settings.llm_model

    # -- Public API ----------------------------------------------------------

    def generate_answer(
        self,
        question: str,
        context: list[Document] | str,
    ) -> str:
        """Generate an answer for *question* using the provided repository *context*.

        Args:
            question: The user's natural-language question.
            context: Retrieved repository context — either a list of
                LangChain ``Document`` objects or a pre-formatted string.

        Returns:
            The generated answer as a string.

        Raises:
            LLMServiceError: If the question is empty, the API call fails,
                or the response is invalid.
        """
        _validate_question(question)

        prompt = self.build_prompt(question, context)

        logger.info("Generating answer for: %s", question[:80])
        try:
            response = self._llm.invoke(prompt)
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)
            raise LLMServiceError(f"Gemini API call failed: {exc}") from exc

        answer = self._extract_text(response)

        if not answer:
            raise LLMServiceError("Gemini returned an empty response")

        logger.info("Answer generated (%d chars)", len(answer))
        return answer

    def build_prompt(
        self,
        question: str,
        context: list[Document] | str,
    ) -> str:
        """Build a formatted prompt from a question and repository context.

        The prompt instructs Gemini to answer using only the supplied context
        and to avoid hallucinating code or project details.

        Args:
            question: The user's natural-language question.
            context: Repository context — ``list[Document]`` or ``str``.

        Returns:
            The fully formatted prompt string.

        Raises:
            LLMServiceError: If the question is empty.
        """
        _validate_question(question)

        context_text = _format_context(context)
        prompt = SYSTEM_PROMPT + CONTEXT_HEADER + context_text + QUESTION_HEADER + question

        logger.debug("Built prompt (%d chars)", len(prompt))
        return prompt

    # -- Internal helpers ----------------------------------------------------

    @staticmethod
    def _extract_text(response: object) -> str:
        """Extract the text content from a LangChain LLM response."""
        if hasattr(response, "content"):
            return str(response.content).strip()
        return str(response).strip()


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _validate_question(question: str) -> None:
    """Raise LLMServiceError if the question is empty or whitespace-only."""
    if not question or not question.strip():
        raise LLMServiceError("Question must not be empty")


def _format_context(context: list[Document] | str) -> str:
    """Convert context into a formatted string for the prompt.

    Each document is rendered with its source file path and content,
    separated by horizontal rules for readability.
    """
    if isinstance(context, str):
        return context.strip() if context.strip() else NO_CONTEXT_NOTICE

    if not context:
        return NO_CONTEXT_NOTICE

    parts: list[str] = []
    for i, doc in enumerate(context, 1):
        file_path = doc.metadata.get("file_path", "unknown")
        file_type = doc.metadata.get("file_type", doc.metadata.get("language", ""))
        header = f"### Source {i}: `{file_path}`"
        code_fence = f"```{file_type}" if file_type else "```"
        parts.append(f"{header}\n{code_fence}\n{doc.page_content}\n```")

    return "\n\n---\n\n".join(parts)

