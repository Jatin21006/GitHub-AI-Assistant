"""
Repository API routes.

Planned endpoints:
- POST /repositories/ingest   — Accept GitHub URL, trigger full ingestion pipeline
- POST /repositories/{repo_id}/query — RAG-based Q&A with source citations
- GET  /repositories/{repo_id}/status — Return ingestion/indexing status
"""
