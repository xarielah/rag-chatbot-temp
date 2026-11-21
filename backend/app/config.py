from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    voyage_api_key: str = ""
    qdrant_url: str = "http://qdrant:6333"
    qdrant_api_key: str | None = None   # empty in development, required in Qdrant Cloud

    collection_name: str = "docs"
    embed_model: str = "voyage-3.5"
    chat_model: str = "claude-haiku-5-5"
    top_k: int = 5
    min_score: float = 0.3
    max_tokens: int = 1024
    docs_dir: str = "/data/docs"
    chunk_size: int = 1000              # characters
    chunk_overlap: int = 150

    # --- chat persistence ---
    chat_ttl_days: int = 30             # sliding: reset on every message
    chat_history_limit: int = 50        # max raw messages sent to the model
    chat_token_budget: int = 50_000     # total (input+output) tokens per chat, hard cap
    chat_summary_every_turns: int = 10  # fold history into a rolling summary every N turns
    chat_summary_max_tokens: int = 400

    # --- database / auth ---
    database_url: str = "postgresql+psycopg://app:app@postgres:5432/app"
    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = ""            # signs the short-lived OAuth state cookie
    session_ttl_days: int = 30
    session_cookie_name: str = "session"
    cookie_secure: bool = True          # set COOKIE_SECURE=false for http://localhost
    google_redirect_uri: str = ""       # empty -> derived from the request URL
    frontend_url: str = "/"             # where to send the user after login
    # comma-separated emails seeded as admins into allowed_emails on startup
    initial_admin_emails: str = ""

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        # Cloud providers (Neon, Supabase, Render, Heroku...) hand out
        # postgres:// or postgresql:// URLs; SQLAlchemy would pick psycopg2
        # (not installed) or reject them. Force the psycopg v3 driver.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v


settings = Settings()