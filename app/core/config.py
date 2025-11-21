from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration."""
    
    # Application
    app_name: str = "HR AI Recruitment Manager"
    debug: bool = False
    environment: str = "development"
    
    # Database
    database_url: str
    database_pool_size: int = 5
    database_max_overflow: int = 10
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # OpenAI
    openai_api_key: str
    
    # LangChain (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str | None = None
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # File Upload
    max_upload_size_mb: int = 10
    allowed_file_types: str = "application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    upload_dir: str = "uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
