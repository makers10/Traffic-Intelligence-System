import logging

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    WEATHER_API_KEY: str = ""
    TRAFFIC_API_KEY: str = ""
    SECRET_KEY: str = "dev-secret"
    DEBUG: bool = True

    # ── Authentication ────────────────────────────────────────────────────
    # API_KEY: general-purpose key for sensors and read-only consumers.
    # OPERATOR_API_KEY: elevated key for operators who can resolve alerts,
    #   trigger training, etc.  Falls back to API_KEY if unset.
    API_KEY: str = ""
    OPERATOR_API_KEY: str = ""

    ALLOWED_ORIGINS: str = "*"  # comma-separated list of allowed origins

    class Config:
        env_file = ".env"

    def get_operator_key(self) -> str:
        """Return the operator key, falling back to the main API key."""
        return self.OPERATOR_API_KEY or self.API_KEY


settings = Settings()

# Warn loudly if auth is disabled outside of explicit debug mode
if not settings.API_KEY and not settings.DEBUG:
    logging.getLogger("app.config").critical(
        "API_KEY is empty and DEBUG is False — the API is UNPROTECTED. "
        "Set API_KEY in your .env or environment variables."
    )
