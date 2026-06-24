"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field


class RepositoryIngestRequest(BaseModel):
    """Request body for ingesting a GitHub repository."""

    github_url: str = Field(
        ...,
        description="GitHub repository URL (HTTPS or owner/repo shorthand)",
        examples=["https://github.com/octocat/Hello-World"],
    )


class RepositoryIngestResponse(BaseModel):
    """Response after attempting to clone and ingest a repository."""

    repository_name: str = Field(..., description="Repository in owner/name format")
    local_path: str = Field(..., description="Absolute path to the cloned repository")
    is_duplicate: bool = Field(
        ...,
        description="True when the repository was already cloned locally",
    )
    message: str = Field(..., description="Human-readable status message")


class Citation(BaseModel):
    """A source citation returned with a RAG answer."""

    file_path: str
    start_line: int
    end_line: int
    snippet: str


class QueryRequest(BaseModel):
    """Request body for a repository Q&A query."""

    question: str = Field(..., min_length=1, description="Natural-language question")


class QueryResponse(BaseModel):
    """RAG answer with supporting source citations."""

    answer: str
    citations: list[Citation] = Field(default_factory=list)


class ParserStats(BaseModel):
    """Statistics collected while parsing and chunking a repository."""

    files_processed: int = Field(..., description="Number of files successfully loaded")
    files_skipped: int = Field(..., description="Number of files skipped during scan or load")
    total_documents: int = Field(..., description="Number of LangChain Document objects created")
    total_chunks: int = Field(..., description="Number of chunks after splitting")
    language_distribution: dict[str, int] = Field(
        default_factory=dict,
        description="Count of processed files grouped by language",
    )


class IndexResult(BaseModel):
    """Result of indexing a repository into the vector store."""

    repository_name: str
    total_documents: int
    total_chunks: int
    total_vectors: int
    vector_store_path: str


class RetrievalResult(BaseModel):
    """A retrieved chunk with similarity score and source metadata."""

    chunk_id: str
    content: str
    score: float
    metadata: dict[str, object] = Field(default_factory=dict)
    file_path: str
    file_name: str
    language: str
    extension: str
