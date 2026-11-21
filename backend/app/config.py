from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None   # empty in development, required in Qdrant Cloud

    collection_name: str = "docs"
    embed_model: str = "voyage-3.5"
    docs_dir: str = "/data/docs"
    chunk_size: int = 1000              # characters
    chunk_overlap: int = 150


settings = Settings()