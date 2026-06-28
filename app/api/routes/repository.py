"""Repository API routes."""

from fastapi import APIRouter, Path

from app.models.schemas import (
    CloneRequest,
    IndexRequest,
    IndexResult,
    QueryResponse,
    RepositoryIngestResponse,
    RepositoryQueryRequest,
    RepositoryStatusResponse,
)
from app.services.clone_service import CloneService
from app.services.embedding_service import EmbeddingService
from app.services.query_service import QueryService
from app.config import get_settings

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/clone", response_model=RepositoryIngestResponse)
async def clone_repository(request: CloneRequest) -> RepositoryIngestResponse:
    """Clone a GitHub repository without fully indexing it."""
    service = CloneService()
    result = service.clone(request.github_url)
    
    return RepositoryIngestResponse(
        repository_name=result.repository_name,
        local_path=str(result.local_path),
        is_duplicate=result.is_duplicate,
        message="Repository cloned successfully" if not result.is_duplicate else "Repository already exists",
    )


@router.post("/index", response_model=IndexResult)
async def index_repository(request: IndexRequest) -> IndexResult:
    """Parse, embed, and build the vector store for a cloned repository."""
    settings = get_settings()
    repo_path = settings.repos_dir / request.repository_name
    
    embedding_service = EmbeddingService()
    return embedding_service.index_repository(repo_path, request.repository_name)


@router.post("/query", response_model=QueryResponse)
async def query_repository(request: RepositoryQueryRequest) -> QueryResponse:
    """Ask a question about a repository using RAG."""
    query_service = QueryService.for_repository(request.repository_name)
    result = query_service.answer_with_context(request.question)
    
    citations = []
    for doc in result.context_documents:
        citations.append({
            "file_path": doc.metadata.get("file_path", "unknown"),
            "start_line": doc.metadata.get("start_line", 0),
            "end_line": doc.metadata.get("end_line", 0),
            "snippet": doc.page_content,
        })
        
    return QueryResponse(
        answer=result.answer,
        citations=citations
    )


@router.get("/{owner}/{repo_name}", response_model=RepositoryStatusResponse)
async def get_repository_status(
    owner: str = Path(..., description="Repository owner"),
    repo_name: str = Path(..., description="Repository name"),
) -> RepositoryStatusResponse:
    """Check the indexing and cloning status of a repository."""
    repository_full_name = f"{owner}/{repo_name}"
    settings = get_settings()
    
    repo_path = settings.repos_dir / owner / repo_name
    vector_store_path = settings.vector_store_dir / owner / repo_name / "index.faiss"
    
    return RepositoryStatusResponse(
        repository_name=repository_full_name,
        is_cloned=repo_path.exists() and repo_path.is_dir(),
        is_indexed=vector_store_path.exists(),
    )
