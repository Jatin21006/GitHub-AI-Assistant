# GitHub Repository AI Assistant

A RAG-powered assistant that clones GitHub repositories, indexes source code with embeddings, and answers questions with source citations.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI |
| AI | LangChain, Google Gemini API |
| Vector Store | FAISS |
| Repository Processing | GitPython |

## Project Structure

```
github-repo-ai-assistant/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Environment & app configuration
│   ├── api/
│   │   └── routes/
│   │       └── repository.py   # REST endpoints (ingest, query)
│   ├── services/
│   │   ├── clone_service.py    # Clone GitHub repos via GitPython
│   │   ├── parser_service.py   # Parse & chunk source code files
│   │   ├── embedding_service.py# Generate embeddings via Gemini
│   │   └── rag_service.py      # RAG pipeline & citation extraction
│   ├── ai/
│   │   ├── llm.py              # LangChain + Gemini LLM wrapper
│   │   └── vector_store.py     # FAISS index management
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   └── utils/
│       └── file_utils.py       # File filtering & path helpers
├── data/
│   ├── repos/                  # Cloned repositories (gitignored)
│   └── vector_stores/          # Persisted FAISS indices (gitignored)
├── tests/
└── requirements.txt
```

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐
│   Client    │────▶│              FastAPI (app/main.py)               │
└─────────────┘     └────────────────────┬─────────────────────────────┘
                                         │
                    ┌────────────────────▼─────────────────────────────┐
                    │           API Routes (app/api/routes)          │
                    │  POST /repositories/ingest                     │
                    │  POST /repositories/{id}/query                 │
                    └────────────────────┬─────────────────────────────┘
                                         │
          ┌──────────────────────────────┼──────────────────────────────┐
          │                              │                              │
          ▼                              ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐          ┌─────────────────┐
│  CloneService   │          │   ParserService     │          │   RAGService    │
│  (GitPython)    │          │   (file chunking)   │          │   (Q&A + cites) │
└────────┬────────┘          └──────────┬──────────┘          └────────┬────────┘
         │                              │                              │
         ▼                              ▼                              ▼
   data/repos/              EmbeddingService                 VectorStore (FAISS)
                             (Gemini embeddings)              + LLM (Gemini)
```

## Data Flow

### 1. Repository Ingestion

1. Client sends a GitHub repository URL.
2. **CloneService** clones the repo into `data/repos/{repo_id}/`.
3. **ParserService** walks the tree, filters source files, and splits them into chunks.
4. **EmbeddingService** generates vector embeddings for each chunk via Gemini.
5. **VectorStore** persists the FAISS index under `data/vector_stores/{repo_id}/`.

### 2. Repository Q&A

1. Client sends a natural-language question for a processed repository.
2. **RAGService** embeds the question and retrieves top-k similar chunks from FAISS.
3. **LLM** (Gemini via LangChain) generates an answer grounded in retrieved context.
4. Response includes the answer and **source citations** (file path, line range, snippet).

## API Endpoints (planned)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/repositories/ingest` | Clone repo, parse, embed, and index |
| `POST` | `/repositories/{repo_id}/query` | Ask a question with RAG |
| `GET`  | `/repositories/{repo_id}/status` | Check ingestion status |
| `GET`  | `/health` | Health check |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # Add your GOOGLE_API_KEY
```

## Development Status

- [x] Project architecture & folder structure
- [ ] Configuration & settings
- [ ] Repository cloning service
- [ ] Source code parser & chunker
- [ ] Embedding generation
- [ ] FAISS vector store
- [ ] RAG Q&A with citations
- [ ] FastAPI routes & integration
- [ ] Tests
