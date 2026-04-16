from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str  # Required — no default, must be set via env
    POS_PROVIDER: str = "stub"
    LABOR_PROVIDER: str = "stub"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "0.1.0"
    # Auth
    JWT_SECRET: str  # Required — no default, must be set via env
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours
    DEMO_MODE: bool = True  # When False, demo endpoints return 404
    DEMO_USER_EMAIL: str = "demo@quantumatiq.com"
    DEMO_USER_PASSWORD: str = "EightySix-Demo-2026"  # Override via env in production

    # Production CORS — override via CORS_ORIGINS env var for dev
    CORS_ORIGINS: list[str] = ["https://quantumatiq.com"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
