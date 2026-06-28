"""Comprehensive test suite for the GeminiLLM service in app.ai.llm."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.ai.llm import (
    CONTEXT_HEADER,
    NO_CONTEXT_NOTICE,
    QUESTION_HEADER,
    SYSTEM_PROMPT,
    GeminiLLM,
    LLMServiceError,
    _format_context,
    _validate_question,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _mock_settings(**overrides: object) -> MagicMock:
    """Create a mock Settings object with sensible defaults."""
    settings = MagicMock()
    settings.gemini_api_key = overrides.get("gemini_api_key", "fake-api-key")
    settings.google_api_key = overrides.get("google_api_key", "")
    settings.llm_model = overrides.get("llm_model", "gemini-2.0-flash")
    settings.embedding_model = overrides.get("embedding_model", "gemini-embedding-2-preview")
    settings.embedding_batch_size = overrides.get("embedding_batch_size", 100)
    settings.embedding_max_retries = overrides.get("embedding_max_retries", 3)
    return settings


def _sample_documents() -> list[Document]:
    """Return sample repository context documents."""
    return [
        Document(
            page_content="def authenticate(user, password):\n    return check_credentials(user, password)",
            metadata={
                "file_path": "src/auth.py",
                "file_type": "python",
                "language": "python",
                "chunk_id": "src/auth.py:0",
            },
        ),
        Document(
            page_content="class UserRepository:\n    def find_by_id(self, user_id):\n        return self.db.query(user_id)",
            metadata={
                "file_path": "src/repository.py",
                "file_type": "python",
                "language": "python",
                "chunk_id": "src/repository.py:0",
            },
        ),
    ]


def _create_llm_with_mock_response(response_text: str) -> GeminiLLM:
    """Create a GeminiLLM instance with a mocked Gemini model."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.content = response_text
        mock_model.invoke.return_value = mock_response
        mock_create.return_value = mock_model

        llm = GeminiLLM(settings=_mock_settings())
        return llm


# ---------------------------------------------------------------------------
# Initialization tests
# ---------------------------------------------------------------------------


def test_gemini_llm_initialization() -> None:
    """GeminiLLM initialises successfully with valid settings."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        llm = GeminiLLM(settings=_mock_settings())
        assert llm.model_name == "gemini-2.0-flash"
    print("  [PASS] GeminiLLM initialised successfully")


def test_gemini_llm_missing_api_key_raises() -> None:
    """GeminiLLM raises LLMServiceError when API key is missing."""
    settings = _mock_settings(gemini_api_key="")
    try:
        GeminiLLM(settings=settings)
        assert False, "Should have raised LLMServiceError"
    except LLMServiceError as exc:
        assert "GEMINI_API_KEY" in str(exc)
    print("  [PASS] Missing API key raises LLMServiceError")


def test_gemini_llm_model_name_property() -> None:
    """model_name returns the configured model."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        llm = GeminiLLM(settings=_mock_settings(llm_model="gemini-2.0-pro"))
        assert llm.model_name == "gemini-2.0-pro"
    print("  [PASS] model_name returns 'gemini-2.0-pro'")


# ---------------------------------------------------------------------------
# Prompt construction tests
# ---------------------------------------------------------------------------


def test_build_prompt_with_documents() -> None:
    """build_prompt includes system prompt, context, and question."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        llm = GeminiLLM(settings=_mock_settings())

    docs = _sample_documents()
    prompt = llm.build_prompt("How does auth work?", docs)

    assert SYSTEM_PROMPT in prompt
    assert CONTEXT_HEADER in prompt
    assert QUESTION_HEADER in prompt
    assert "How does auth work?" in prompt
    assert "src/auth.py" in prompt
    assert "src/repository.py" in prompt
    assert "authenticate" in prompt
    print("  [PASS] build_prompt includes all expected sections")


def test_build_prompt_with_string_context() -> None:
    """build_prompt accepts a plain string as context."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        llm = GeminiLLM(settings=_mock_settings())

    context_str = "This repo uses FastAPI for the web layer."
    prompt = llm.build_prompt("What framework is used?", context_str)

    assert "FastAPI" in prompt
    assert "What framework is used?" in prompt
    print("  [PASS] build_prompt works with string context")


def test_build_prompt_with_empty_context() -> None:
    """build_prompt inserts NO_CONTEXT_NOTICE when context is empty."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        llm = GeminiLLM(settings=_mock_settings())

    prompt = llm.build_prompt("What is this?", [])
    assert NO_CONTEXT_NOTICE in prompt

    prompt2 = llm.build_prompt("What is this?", "")
    assert NO_CONTEXT_NOTICE in prompt2

    prompt3 = llm.build_prompt("What is this?", "   ")
    assert NO_CONTEXT_NOTICE in prompt3

    print("  [PASS] Empty context produces NO_CONTEXT_NOTICE")


def test_build_prompt_empty_question_raises() -> None:
    """build_prompt raises LLMServiceError for empty question."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        llm = GeminiLLM(settings=_mock_settings())

    for empty_q in ["", "   ", None]:
        try:
            llm.build_prompt(empty_q, "some context")
            assert False, f"Should have raised for question={empty_q!r}"
        except (LLMServiceError, TypeError, AttributeError):
            pass
    print("  [PASS] Empty questions raise LLMServiceError")


# ---------------------------------------------------------------------------
# Answer generation tests
# ---------------------------------------------------------------------------


def test_generate_answer_success() -> None:
    """generate_answer returns the model's response text."""
    llm = _create_llm_with_mock_response("The authenticate function validates user credentials.")
    docs = _sample_documents()
    answer = llm.generate_answer("How does auth work?", docs)
    assert "authenticate" in answer
    assert len(answer) > 0
    print(f"  [PASS] generate_answer returned: {answer[:60]}...")


def test_generate_answer_with_string_context() -> None:
    """generate_answer works with string context."""
    llm = _create_llm_with_mock_response("FastAPI is the web framework.")
    answer = llm.generate_answer("What framework?", "Uses FastAPI.")
    assert "FastAPI" in answer
    print("  [PASS] generate_answer works with string context")


def test_generate_answer_empty_question_raises() -> None:
    """generate_answer raises LLMServiceError for empty question."""
    llm = _create_llm_with_mock_response("should not reach here")
    try:
        llm.generate_answer("", _sample_documents())
        assert False, "Should have raised LLMServiceError"
    except LLMServiceError:
        pass
    try:
        llm.generate_answer("   ", _sample_documents())
        assert False, "Should have raised for whitespace"
    except LLMServiceError:
        pass
    print("  [PASS] Empty question raises LLMServiceError")


def test_generate_answer_empty_context() -> None:
    """generate_answer still works with empty context (includes notice)."""
    llm = _create_llm_with_mock_response("I cannot answer without context.")
    answer = llm.generate_answer("What does this do?", [])
    assert len(answer) > 0
    print("  [PASS] generate_answer with empty context returns response")


def test_generate_answer_api_failure_raises() -> None:
    """generate_answer raises LLMServiceError when Gemini API fails."""
    with patch("app.ai.llm._create_llm") as mock_create:
        mock_model = MagicMock()
        mock_model.invoke.side_effect = RuntimeError("API quota exceeded")
        mock_create.return_value = mock_model

        llm = GeminiLLM(settings=_mock_settings())
        try:
            llm.generate_answer("test question", "test context")
            assert False, "Should have raised LLMServiceError"
        except LLMServiceError as exc:
            assert "API" in str(exc)
    print("  [PASS] API failure raises LLMServiceError")


def test_generate_answer_empty_response_raises() -> None:
    """generate_answer raises LLMServiceError when Gemini returns empty."""
    llm = _create_llm_with_mock_response("")
    try:
        llm.generate_answer("What is this?", "some context")
        assert False, "Should have raised LLMServiceError"
    except LLMServiceError as exc:
        assert "empty" in str(exc).lower()
    print("  [PASS] Empty Gemini response raises LLMServiceError")


def test_generate_answer_whitespace_response_raises() -> None:
    """generate_answer raises LLMServiceError when response is whitespace only."""
    llm = _create_llm_with_mock_response("   \n  ")
    try:
        llm.generate_answer("What is this?", "some context")
        assert False, "Should have raised LLMServiceError"
    except LLMServiceError as exc:
        assert "empty" in str(exc).lower()
    print("  [PASS] Whitespace-only response raises LLMServiceError")


# ---------------------------------------------------------------------------
# _format_context tests
# ---------------------------------------------------------------------------


def test_format_context_with_documents() -> None:
    """_format_context formats Document objects with file paths and code fences."""
    docs = _sample_documents()
    result = _format_context(docs)
    assert "src/auth.py" in result
    assert "src/repository.py" in result
    assert "```python" in result
    assert "authenticate" in result
    assert "---" in result  # separator between documents
    print("  [PASS] _format_context produces correct Document format")


def test_format_context_with_string() -> None:
    """_format_context passes through non-empty strings."""
    result = _format_context("inline context text")
    assert result == "inline context text"
    print("  [PASS] _format_context passes through string")


def test_format_context_empty_list() -> None:
    """_format_context returns NO_CONTEXT_NOTICE for empty list."""
    assert _format_context([]) == NO_CONTEXT_NOTICE
    print("  [PASS] Empty list produces NO_CONTEXT_NOTICE")


def test_format_context_empty_string() -> None:
    """_format_context returns NO_CONTEXT_NOTICE for empty/whitespace string."""
    assert _format_context("") == NO_CONTEXT_NOTICE
    assert _format_context("   ") == NO_CONTEXT_NOTICE
    print("  [PASS] Empty/whitespace string produces NO_CONTEXT_NOTICE")


# ---------------------------------------------------------------------------
# _validate_question tests
# ---------------------------------------------------------------------------


def test_validate_question_valid() -> None:
    """_validate_question passes for non-empty strings."""
    _validate_question("What is this?")
    _validate_question("a")
    print("  [PASS] Valid questions pass validation")


def test_validate_question_empty_raises() -> None:
    """_validate_question raises for empty/whitespace strings."""
    for invalid in ["", "   ", "\n\t"]:
        try:
            _validate_question(invalid)
            assert False, f"Should have raised for {invalid!r}"
        except LLMServiceError:
            pass
    print("  [PASS] Empty/whitespace questions raise LLMServiceError")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        # Initialization
        ("GeminiLLM initialization", test_gemini_llm_initialization),
        ("Missing API key raises", test_gemini_llm_missing_api_key_raises),
        ("model_name property", test_gemini_llm_model_name_property),
        # Prompt construction
        ("build_prompt with documents", test_build_prompt_with_documents),
        ("build_prompt with string context", test_build_prompt_with_string_context),
        ("build_prompt with empty context", test_build_prompt_with_empty_context),
        ("build_prompt empty question raises", test_build_prompt_empty_question_raises),
        # Answer generation
        ("generate_answer success", test_generate_answer_success),
        ("generate_answer with string context", test_generate_answer_with_string_context),
        ("generate_answer empty question raises", test_generate_answer_empty_question_raises),
        ("generate_answer empty context", test_generate_answer_empty_context),
        ("generate_answer API failure raises", test_generate_answer_api_failure_raises),
        ("generate_answer empty response raises", test_generate_answer_empty_response_raises),
        ("generate_answer whitespace response raises", test_generate_answer_whitespace_response_raises),
        # _format_context
        ("_format_context with documents", test_format_context_with_documents),
        ("_format_context with string", test_format_context_with_string),
        ("_format_context empty list", test_format_context_empty_list),
        ("_format_context empty string", test_format_context_empty_string),
        # _validate_question
        ("_validate_question valid", test_validate_question_valid),
        ("_validate_question empty raises", test_validate_question_empty_raises),
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
