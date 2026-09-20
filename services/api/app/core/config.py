from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "University Central Platform & API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://uni_admin:uni_secure_password@postgres:5432/university_platform"
    DATABASE_SSL_MODE: str = "disable"
    REDIS_URL: str = ""
    JWT_SECRET: str = "development_secret_key_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:8080,http://localhost:3000"
    AUTO_CREATE_SCHEMA: bool = False
    SEED_DEMO_DATA: bool = False
    AI_ENABLED: bool = False
    AI_BASE_URL: str = "https://api.openai.com/v1"
    AI_MODEL: str = "gpt-4o-mini"
    AI_FALLBACK_MODELS: str = ""
    DEFAULT_API_KEY: str = ""
    FRAPPE_EDUCATION_BASE_URL: str = ""
    FRAPPE_EDUCATION_API_KEY: str = ""
    FRAPPE_EDUCATION_API_SECRET: str = ""
    FRAPPE_EDUCATION_STUDENT_NUMBER_FIELD: str = "student_number"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
