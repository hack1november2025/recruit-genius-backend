"""Logging configuration for the application."""
import logging
import sys
from pathlib import Path
from app.core.config import get_settings


def setup_logging():
    """Configure application logging."""
    settings = get_settings()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Handlers
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_dir / "app.log")
    ]
    
    # Basic config
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    # Create specialized loggers
    loggers = {
        "llm": logging.getLogger("llm"),
        "rag": logging.getLogger("rag"),
        "api": logging.getLogger("api"),
        "cv_parser": logging.getLogger("cv_parser"),
        "metrics": logging.getLogger("metrics"),
    }
    
    for logger in loggers.values():
        logger.setLevel(log_level)
    
    return loggers


# Initialize loggers
loggers = setup_logging()

# Export for easy import
llm_logger = loggers["llm"]
rag_logger = loggers["rag"]
api_logger = loggers["api"]
cv_parser_logger = loggers["cv_parser"]
metrics_logger = loggers["metrics"]
