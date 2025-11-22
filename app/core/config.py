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
    
    # OpenAI
    openai_api_key: str
    
    # LLM Models
    llm_model: str = "gpt-4o"  # Model for general agents (job generator, recruiter, etc.)
    llm_rag_model: str = "gpt-4o"  # Model for RAG/chat agents (cv_chat)
    
    # LangChain (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str | None = None
    
    # Langfuse
    langfuse_enabled: bool = True
    langfuse_public_key: str = "pk-lf-78506f8d-de33-4560-8678-ca83a92f21d2"
    langfuse_secret_key: str = "sk-lf-1dea372d-3dd5-44d1-a43f-df3edc44fc4a"
    langfuse_host: str = "https://llminsights.abbaflow.com"
    
    # Optional Redis URL (may be provided in environment)
    redis_url: str | None = None
    # Telegram
    telegram_bot_token: str | None = None
    
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
