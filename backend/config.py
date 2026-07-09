"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Athena backend.

    All values are loaded from environment variables or a .env file.
    """

    # --- LLM ---
    gemini_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # --- Database ---
    database_url: str = "postgresql+asyncpg://athena:athena_secret@localhost:5432/athena_db"

    # --- ChromaDB ---
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "athena_documents"

    # --- App ---
    backend_url: str = "http://localhost:8000"
    frontend_port: int = 8501
    log_level: str = "INFO"

    # --- Retrieval ---
    retrieval_top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Singleton instance — import this everywhere
settings = Settings()
