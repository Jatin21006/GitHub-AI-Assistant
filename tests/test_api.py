"""Integration tests for FastAPI API layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.clone_service import CloneError
from app.services.parser_service import ParserError

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    print("  [PASS] GET /health returned 200 OK")


# ---------------------------------------------------------------------------
# Clone endpoint
# ---------------------------------------------------------------------------

@patch("app.api.routes.repository.CloneService")
def test_clone_repository_success(mock_clone_cls) -> None:
    mock_service = MagicMock()
    mock_result = MagicMock()
    mock_result.repository_name = "octocat/Hello-World"
    mock_result.local_path = "/tmp/octocat/Hello-World"
    mock_result.is_duplicate = False
    mock_service.clone.return_value = mock_result
    mock_clone_cls.return_value = mock_service

    response = client.post(
        "/repositories/clone",
        json={"github_url": "https://github.com/octocat/Hello-World"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["repository_name"] == "octocat/Hello-World"
    assert data["local_path"] == "/tmp/octocat/Hello-World"
    assert data["is_duplicate"] is False
    assert "successfully" in data["message"]
    print("  [PASS] POST /repositories/clone returned success")


@patch("app.api.routes.repository.CloneService")
def test_clone_repository_failure(mock_clone_cls) -> None:
    mock_service = MagicMock()
    mock_service.clone.side_effect = CloneError("Invalid URL")
    mock_clone_cls.return_value = mock_service

    response = client.post(
        "/repositories/clone",
        json={"github_url": "invalid"}
    )
    assert response.status_code == 400
    assert "Invalid URL" in response.json()["detail"]
    print("  [PASS] POST /repositories/clone returns 400 on CloneError")


# ---------------------------------------------------------------------------
# Index endpoint
# ---------------------------------------------------------------------------

@patch("app.api.routes.repository.EmbeddingService")
def test_index_repository_success(mock_embed_cls) -> None:
    mock_service = MagicMock()
    mock_result = MagicMock()
    mock_result.repository_name = "owner/repo"
    mock_result.total_documents = 2
    mock_result.total_chunks = 2
    mock_result.total_vectors = 2
    mock_result.vector_store_path = "/tmp/vector_store"
    
    mock_service.index_repository.return_value = mock_result
    mock_embed_cls.return_value = mock_service
    
    response = client.post(
        "/repositories/index",
        json={"repository_name": "owner/repo"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["repository_name"] == "owner/repo"
    assert data["total_documents"] == 2
    assert data["total_chunks"] == 2
    assert data["total_vectors"] == 2
    assert data["vector_store_path"] == "/tmp/vector_store"
    print("  [PASS] POST /repositories/index returned success")


@patch("app.api.routes.repository.EmbeddingService")
def test_index_repository_parser_error(mock_embed_cls) -> None:
    mock_service = MagicMock()
    mock_service.index_repository.side_effect = ParserError("Repository not found locally")
    mock_embed_cls.return_value = mock_service
    
    response = client.post(
        "/repositories/index",
        json={"repository_name": "owner/repo"}
    )
    assert response.status_code == 400
    assert "not found locally" in response.json()["detail"]
    print("  [PASS] POST /repositories/index returns 400 on ParserError")


# ---------------------------------------------------------------------------
# Query endpoint
# ---------------------------------------------------------------------------

@patch("app.api.routes.repository.QueryService")
def test_query_repository_success(mock_query_cls) -> None:
    mock_service = MagicMock()
    mock_result = MagicMock()
    mock_result.answer = "The answer is 42."
    
    mock_doc = MagicMock()
    mock_doc.metadata = {"file_path": "main.py", "start_line": 1, "end_line": 5}
    mock_doc.page_content = "x = 42"
    mock_result.context_documents = [mock_doc]
    
    mock_service.answer_with_context.return_value = mock_result
    mock_query_cls.for_repository.return_value = mock_service
    
    response = client.post(
        "/repositories/query",
        json={"repository_name": "owner/repo", "question": "What is the answer?"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The answer is 42."
    assert len(data["citations"]) == 1
    assert data["citations"][0]["file_path"] == "main.py"
    assert data["citations"][0]["snippet"] == "x = 42"
    print("  [PASS] POST /repositories/query returned success")


# ---------------------------------------------------------------------------
# Status endpoint
# ---------------------------------------------------------------------------

@patch("app.api.routes.repository.get_settings")
def test_get_repository_status(mock_get_settings) -> None:
    mock_settings = MagicMock()
    
    # We will mock the Path objects returned by settings
    mock_repos_dir = MagicMock()
    mock_vector_dir = MagicMock()
    
    mock_settings.repos_dir = mock_repos_dir
    mock_settings.vector_store_dir = mock_vector_dir
    
    mock_get_settings.return_value = mock_settings
    
    # Mock repos_dir / owner / repo_name .exists() and .is_dir()
    mock_repo_path = MagicMock()
    mock_repo_path.exists.return_value = True
    mock_repo_path.is_dir.return_value = True
    mock_repos_dir.__truediv__.return_value.__truediv__.return_value = mock_repo_path
    
    # Mock vector_store_dir / owner / repo_name / "index.faiss" .exists()
    mock_vector_path = MagicMock()
    mock_vector_path.exists.return_value = False
    mock_vector_dir.__truediv__.return_value.__truediv__.return_value.__truediv__.return_value = mock_vector_path
    
    response = client.get("/repositories/owner/repo")
    
    assert response.status_code == 200
    data = response.json()
    assert data["repository_name"] == "owner/repo"
    assert data["is_cloned"] is True
    assert data["is_indexed"] is False
    print("  [PASS] GET /repositories/{owner}/{repo} returned correct status")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [
        ("Health Check", test_health_check),
        ("Clone repository success", test_clone_repository_success),
        ("Clone repository failure", test_clone_repository_failure),
        ("Index repository success", test_index_repository_success),
        ("Index repository failure", test_index_repository_parser_error),
        ("Query repository success", test_query_repository_success),
        ("Get repository status", test_get_repository_status),
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
