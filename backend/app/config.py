from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    WEATHER_API_KEY: str = ""
    TRAFFIC_API_KEY: str = ""
    SECRET_KEY: str = "dev-secret"
    DEBUG: bool = True
    API_KEY: str = ""           # set in .env to enable auth
    ALLOWED_ORIGINS: str = "*"  # comma-separated list of allowed origins

    class Config:
        env_file = ".env"

settings = Settings()
