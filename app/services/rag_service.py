"""
Retrieval-Augmented Generation (RAG) service.

Responsibilities:
- Orchestrate the full Q&A pipeline:
  1. Embed user question
  2. Retrieve top-k relevant chunks from FAISS
  3. Build prompt with retrieved context
  4. Generate answer via Gemini LLM
  5. Extract and return source citations (file, lines, snippet)
"""
