"""Comprehensive test suite for app.services.query_service module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.services.query_service import (
    DEFAULT_K,
    QueryResult,
    QueryService,
    QueryServiceError,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _sample_documents() -> list[Document]:
    """Return sample retrieved documents."""
    return [
        Document(
            page_content="def authenticate(user, password):\n    return check_credentials(user, password)",
            metadata={
                "file_path": "src/auth.py",
                "file_type": "python",
                "chunk_id": "src/auth.py:0",
            },
        ),
        Document(
            page_content="class UserRepository:\n    def find_by_id(self, user_id):\n        return self.db.query(user_id)",
            metadata={
                "file_path": "src/repository.py",
                "file_type": "python",
                "chunk_id": "src/repository.py:0",
            },
        ),
        Document(
            page_content="# API Documentation\n\nREST endpoints for user management.",
            metadata={
                "file_path": "docs/api.md",
                "file_type": "markdown",
                "chunk_id": "docs/api.md:0",
            },
        ),
    ]


def _mock_retriever(documents: list[Document] | None = None) -> MagicMock:
    """Create a mock RetrieverService that returns sample documents."""
    mock = MagicMock()
    mock.search.return_value = documents if documents is not None else _sample_documents()
    return mock


def _mock_llm(answer: str = "The authenticate function validates credentials.") -> MagicMock:
    """Create a mock GeminiLLM that returns a fixed answer."""
    mock = MagicMock()
    mock.generate_answer.return_value = answer
    return mock


def _build_query_service(
    retriever: MagicMock | None = None,
    llm: MagicMock | None = None,
    default_k: int = DEFAULT_K,
) -> QueryService:
    """Build a QueryService with mock dependencies."""
    return QueryService(
        retriever=retriever or _mock_retriever(),
        llm=llm or _mock_llm(),
        default_k=default_k,
    )


# ---------------------------------------------------------------------------
# End-to-end pipeline tests
# ---------------------------------------------------------------------------


def test_answer_returns_string() -> None:
    """answer() returns the LLM answer as a plain string."""
    service = _build_query_service()
    result = service.answer("How does auth work?")
    assert isinstance(result, str)
    assert "authenticate" in result
    print(f"  [PASS] answer() returned: {result[:50]}...")


def test_answer_with_context_returns_query_result() -> None:
    """answer_with_context() returns a QueryResult with all fields."""
    service = _build_query_service()
    result = service.answer_with_context("How does auth work?")
    assert isinstance(result, QueryResult)
    assert isinstance(result.answer, str)
    assert result.question == "How does auth work?"
    assert len(result.context_documents) == 3
    assert result.num_documents_retrieved == 3
    print("  [PASS] answer_with_context() returned complete QueryResult")


def test_pipeline_calls_retriever_then_llm() -> None:
    """The pipeline calls retriever.search() then llm.generate_answer()."""
    retriever = _mock_retriever()
    llm = _mock_llm()
    service = QueryService(retriever, llm)

    service.answer("test question")

    retriever.search.assert_called_once_with("test question", k=DEFAULT_K)
    llm.generate_answer.assert_called_once()

    # Verify the LLM received the question and retrieved documents
    call_args = llm.generate_answer.call_args
    assert call_args[0][0] == "test question"
    assert len(call_args[0][1]) == 3  # 3 sample documents
    print("  [PASS] Pipeline calls retriever then LLM in order")


def test_retrieved_documents_passed_to_llm() -> None:
    """Documents from the retriever are passed as context to the LLM."""
    docs = _sample_documents()
    retriever = _mock_retriever(docs)
    llm = _mock_llm()
    service = QueryService(retriever, llm)

    service.answer("question")

    call_args = llm.generate_answer.call_args
    context = call_args[0][1]
    assert context is docs
    print("  [PASS] Exact retriever documents passed to LLM")


# ---------------------------------------------------------------------------
# Configurable k tests
# ---------------------------------------------------------------------------


def test_default_k() -> None:
    """answer() uses DEFAULT_K when k is not specified."""
    retriever = _mock_retriever()
    service = _build_query_service(retriever=retriever)

    service.answer("question")

    retriever.search.assert_called_once_with("question", k=DEFAULT_K)
    print(f"  [PASS] Default k={DEFAULT_K} used")


def test_custom_k() -> None:
    """answer() passes custom k to the retriever."""
    retriever = _mock_retriever()
    service = _build_query_service(retriever=retriever)

    service.answer("question", k=3)

    retriever.search.assert_called_once_with("question", k=3)
    print("  [PASS] Custom k=3 passed to retriever")


def test_custom_default_k() -> None:
    """QueryService accepts a custom default_k at construction."""
    retriever = _mock_retriever()
    service = _build_query_service(retriever=retriever, default_k=10)

    service.answer("question")

    retriever.search.assert_called_once_with("question", k=10)
    print("  [PASS] Custom default_k=10 used")


# ---------------------------------------------------------------------------
# QueryResult tests
# ---------------------------------------------------------------------------


def test_query_result_fields() -> None:
    """QueryResult contains all expected fields."""
    docs = _sample_documents()
    result = QueryResult(
        answer="Test answer",
        question="Test question",
        context_documents=docs,
        num_documents_retrieved=len(docs),
    )
    assert result.answer == "Test answer"
    assert result.question == "Test question"
    assert len(result.context_documents) == 3
    assert result.num_documents_retrieved == 3
    print("  [PASS] QueryResult fields correct")


def test_query_result_defaults() -> None:
    """QueryResult has sensible defaults for optional fields."""
    result = QueryResult(answer="answer", question="q")
    assert result.context_documents == []
    assert result.num_documents_retrieved == 0
    print("  [PASS] QueryResult defaults correct")


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


def test_empty_question_raises() -> None:
    """answer() raises QueryServiceError for empty question."""
    service = _build_query_service()
    for empty_q in ["", "   ", "\n\t"]:
        try:
            service.answer(empty_q)
            assert False, f"Should have raised for question={empty_q!r}"
        except QueryServiceError as exc:
            assert "empty" in str(exc).lower()
    print("  [PASS] Empty questions raise QueryServiceError")


def test_retriever_failure_raises() -> None:
    """answer() raises QueryServiceError when retriever fails."""
    from app.services.retriever import RetrieverError

    retriever = MagicMock()
    retriever.search.side_effect = RetrieverError("FAISS index corrupt")
    service = QueryService(retriever, _mock_llm())

    try:
        service.answer("question")
        assert False, "Should have raised QueryServiceError"
    except QueryServiceError as exc:
        assert "retrieval" in str(exc).lower()
        assert "FAISS index corrupt" in str(exc)
    print("  [PASS] Retriever failure wrapped in QueryServiceError")


def test_retriever_unexpected_error_raises() -> None:
    """answer() wraps unexpected retriever exceptions."""
    retriever = MagicMock()
    retriever.search.side_effect = RuntimeError("unexpected crash")
    service = QueryService(retriever, _mock_llm())

    try:
        service.answer("question")
        assert False, "Should have raised QueryServiceError"
    except QueryServiceError as exc:
        assert "unexpected" in str(exc).lower()
    print("  [PASS] Unexpected retriever error wrapped in QueryServiceError")


def test_llm_failure_raises() -> None:
    """answer() raises QueryServiceError when LLM fails."""
    from app.ai.llm import LLMServiceError

    llm = MagicMock()
    llm.generate_answer.side_effect = LLMServiceError("API rate limited")
    service = QueryService(_mock_retriever(), llm)

    try:
        service.answer("question")
        assert False, "Should have raised QueryServiceError"
    except QueryServiceError as exc:
        assert "llm" in str(exc).lower()
        assert "API rate limited" in str(exc)
    print("  [PASS] LLM failure wrapped in QueryServiceError")


def test_llm_unexpected_error_raises() -> None:
    """answer() wraps unexpected LLM exceptions."""
    llm = MagicMock()
    llm.generate_answer.side_effect = RuntimeError("something broke")
    service = QueryService(_mock_retriever(), llm)

    try:
        service.answer("question")
        assert False, "Should have raised QueryServiceError"
    except QueryServiceError as exc:
        assert "unexpected" in str(exc).lower()
    print("  [PASS] Unexpected LLM error wrapped in QueryServiceError")


# ---------------------------------------------------------------------------
# Factory constructor tests
# ---------------------------------------------------------------------------


def test_for_repository_success() -> None:
    """for_repository() creates a working QueryService."""
    with patch("app.services.query_service.RetrieverService") as mock_ret_cls, \
         patch("app.services.query_service.GeminiLLM") as mock_llm_cls:
        mock_ret_cls.from_repository.return_value = _mock_retriever()
        mock_llm_cls.return_value = _mock_llm()

        service = QueryService.for_repository("owner/repo")
        result = service.answer("test question")
        assert isinstance(result, str)

    print("  [PASS] for_repository() creates working service")


def test_for_repository_retriever_failure() -> None:
    """for_repository() raises QueryServiceError when retriever fails."""
    from app.services.retriever import RetrieverError

    with patch("app.services.query_service.RetrieverService") as mock_ret_cls:
        mock_ret_cls.from_repository.side_effect = RetrieverError("no index")

        try:
            QueryService.for_repository("owner/repo")
            assert False, "Should have raised QueryServiceError"
        except QueryServiceError as exc:
            assert "retriever" in str(exc).lower()
    print("  [PASS] for_repository() wraps retriever errors")


def test_for_repository_llm_failure() -> None:
    """for_repository() raises QueryServiceError when LLM init fails."""
    from app.ai.llm import LLMServiceError

    with patch("app.services.query_service.RetrieverService") as mock_ret_cls, \
         patch("app.services.query_service.GeminiLLM") as mock_llm_cls:
        mock_ret_cls.from_repository.return_value = _mock_retriever()
        mock_llm_cls.side_effect = LLMServiceError("no API key")

        try:
            QueryService.for_repository("owner/repo")
            assert False, "Should have raised QueryServiceError"
        except QueryServiceError as exc:
            assert "llm" in str(exc).lower()
    print("  [PASS] for_repository() wraps LLM init errors")


def test_from_path_success() -> None:
    """from_path() creates a working QueryService."""
    with patch("app.services.query_service.RetrieverService") as mock_ret_cls, \
         patch("app.services.query_service.GeminiLLM") as mock_llm_cls:
        mock_ret_cls.from_path.return_value = _mock_retriever()
        mock_llm_cls.return_value = _mock_llm()

        service = QueryService.from_path("/fake/path")
        result = service.answer("test question")
        assert isinstance(result, str)

    print("  [PASS] from_path() creates working service")


# ---------------------------------------------------------------------------
# Empty retrieval tests
# ---------------------------------------------------------------------------


def test_empty_retrieval_still_calls_llm() -> None:
    """When retriever returns zero documents, LLM is still called."""
    retriever = _mock_retriever(documents=[])
    llm = _mock_llm(answer="No relevant code found for your question.")
    service = QueryService(retriever, llm)

    result = service.answer_with_context("obscure question")
    assert result.num_documents_retrieved == 0
    assert "No relevant code" in result.answer
    llm.generate_answer.assert_called_once()
    print("  [PASS] Empty retrieval still invokes LLM")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        # End-to-end
        ("answer returns string", test_answer_returns_string),
        ("answer_with_context returns QueryResult", test_answer_with_context_returns_query_result),
        ("pipeline calls retriever then LLM", test_pipeline_calls_retriever_then_llm),
        ("retrieved docs passed to LLM", test_retrieved_documents_passed_to_llm),
        # Configurable k
        ("default k", test_default_k),
        ("custom k", test_custom_k),
        ("custom default_k", test_custom_default_k),
        # QueryResult
        ("QueryResult fields", test_query_result_fields),
        ("QueryResult defaults", test_query_result_defaults),
        # Error handling
        ("empty question raises", test_empty_question_raises),
        ("retriever failure raises", test_retriever_failure_raises),
        ("retriever unexpected error raises", test_retriever_unexpected_error_raises),
        ("LLM failure raises", test_llm_failure_raises),
        ("LLM unexpected error raises", test_llm_unexpected_error_raises),
        # Factory constructors
        ("for_repository success", test_for_repository_success),
        ("for_repository retriever failure", test_for_repository_retriever_failure),
        ("for_repository LLM failure", test_for_repository_llm_failure),
        ("from_path success", test_from_path_success),
        # Edge cases
        ("empty retrieval still calls LLM", test_empty_retrieval_still_calls_llm),
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
