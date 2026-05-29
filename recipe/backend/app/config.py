from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "sqlite:///./recipes.db"

    # Auth
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # one week

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Redis (optional). When set, the parse rate limiter is enforced globally
    # across all workers/instances. Unset -> in-memory per-process limiter.
    redis_url: str = ""

    # Parse endpoint limits
    parse_rate_limit_per_hour: int = 20
    max_text_length: int = 20_000
    fetch_timeout_seconds: float = 5.0
    max_fetch_bytes: int = 2 * 1024 * 1024  # 2 MB
    max_redirects: int = 3

    # CORS
    cors_origins: str = "*"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
