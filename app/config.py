"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings sourced from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    google_api_key: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    repos_dir: Path = Field(default=PROJECT_ROOT / "data" / "repos", validation_alias="REPOS_DIR")
    vector_store_dir: Path = Field(
        default=PROJECT_ROOT / "data" / "vector_stores",
        validation_alias="VECTOR_STORE_DIR",
    )
    embedding_model: str = Field(default="gemini-embedding-2-preview", validation_alias="EMBEDDING_MODEL")
    embedding_batch_size: int = Field(default=100, validation_alias="EMBEDDING_BATCH_SIZE")
    embedding_max_retries: int = Field(default=3, validation_alias="EMBEDDING_MAX_RETRIES")
    llm_model: str = Field(default="gemini-2.0-flash", validation_alias="LLM_MODEL")

    def model_post_init(self, __context: object) -> None:
        if not self.gemini_api_key and self.google_api_key:
            self.gemini_api_key = self.google_api_key
        self.repos_dir = _resolve_path(self.repos_dir)
        self.vector_store_dir = _resolve_path(self.vector_store_dir)
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)


def _resolve_path(path: Path) -> Path:
    """Resolve relative paths against the project root."""
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
