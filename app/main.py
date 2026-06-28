"""
FastAPI application entry point.

Responsibilities:
- Create and configure the FastAPI app instance
- Register API routers
- Configure CORS and middleware
- Mount health-check endpoint
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, repository
from app.services.clone_service import CloneError
from app.services.parser_service import ParserError
from app.services.vector_store import VectorStoreError
from app.services.retriever import RetrieverError
from app.ai.llm import LLMServiceError
from app.services.query_service import QueryServiceError

app = FastAPI(
    title="GitHub Repository AI Assistant API",
    description="API for ingesting and querying GitHub repositories using RAG.",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(repository.router)


# Exception Handlers
@app.exception_handler(CloneError)
async def clone_error_handler(request: Request, exc: CloneError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(ParserError)
async def parser_error_handler(request: Request, exc: ParserError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(VectorStoreError)
async def vector_store_error_handler(request: Request, exc: VectorStoreError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(RetrieverError)
async def retriever_error_handler(request: Request, exc: RetrieverError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(LLMServiceError)
async def llm_service_error_handler(request: Request, exc: LLMServiceError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(QueryServiceError)
async def query_service_error_handler(request: Request, exc: QueryServiceError):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
