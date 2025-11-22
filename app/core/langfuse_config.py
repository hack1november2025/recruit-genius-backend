"""Langfuse integration for LLM observability."""
import os
from typing import Optional
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from app.core.config import get_settings
from app.core.logging import llm_logger


# Global Langfuse instance
_langfuse_instance: Optional[Langfuse] = None
_env_configured = False


def _configure_langfuse_env():
    """Configure Langfuse environment variables."""
    global _env_configured
    
    if _env_configured:
        return
    
    settings = get_settings()
    
    if settings.langfuse_enabled:
        # Set environment variables for Langfuse
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        _env_configured = True
        llm_logger.info(f"Langfuse environment configured with host: {settings.langfuse_host}")


def get_langfuse_client() -> Optional[Langfuse]:
    """
    Get or create the global Langfuse client instance.
    
    Returns:
        Langfuse client if enabled, None otherwise
    """
    global _langfuse_instance
    
    settings = get_settings()
    
    if not settings.langfuse_enabled:
        return None
    
    if _langfuse_instance is None:
        try:
            _configure_langfuse_env()
            _langfuse_instance = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host
            )
            llm_logger.info(f"Langfuse client initialized with host: {settings.langfuse_host}")
        except Exception as e:
            llm_logger.error(f"Failed to initialize Langfuse client: {e}")
            return None
    
    return _langfuse_instance


def get_langfuse_handler(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_name: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None
) -> Optional[CallbackHandler]:
    """
    Create a new Langfuse callback handler for LangChain operations.
    
    This handler tracks all LLM calls made through LangChain.
    
    Args:
        session_id: Session ID for grouping related traces
        user_id: User ID for attribution
        trace_name: Human-readable name for the trace
        tags: List of tags for filtering and organization
        metadata: Additional metadata to attach to the trace
        
    Returns:
        CallbackHandler if Langfuse is enabled, None otherwise
    """
    settings = get_settings()
    
    if not settings.langfuse_enabled:
        return None
    
    try:
        # Ensure environment is configured
        _configure_langfuse_env()
        
        # Create handler with optional trace metadata
        handler = CallbackHandler()
        
        # If we have trace metadata, we need to set it on the handler
        # The new API uses trace context which is set via config in the invoke call
        if session_id:
            handler.session_id = session_id
        if user_id:
            handler.user_id = user_id
        if trace_name:
            handler.trace_name = trace_name
        if tags:
            handler.tags = tags
        if metadata:
            handler.metadata = metadata
            
        return handler
    except Exception as e:
        llm_logger.error(f"Failed to create Langfuse handler: {e}")
        return None


def get_langfuse_callbacks(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    trace_name: Optional[str] = None,
    tags: Optional[list[str]] = None,
    metadata: Optional[dict] = None
) -> list:
    """
    Get list of callbacks including Langfuse handler.
    
    This is a convenience function that returns a list of callbacks
    ready to be passed to LangChain's invoke/ainvoke methods.
    
    Args:
        session_id: Session ID for grouping related traces
        user_id: User ID for attribution
        trace_name: Human-readable name for the trace
        tags: List of tags for filtering and organization
        metadata: Additional metadata to attach to the trace
        
    Returns:
        List of callback handlers (empty list if Langfuse is disabled)
    """
    handler = get_langfuse_handler(
        session_id=session_id,
        user_id=user_id,
        trace_name=trace_name,
        tags=tags,
        metadata=metadata
    )
    
    return [handler] if handler else []


def flush_langfuse():
    """
    Flush Langfuse client to ensure all traces are sent.
    
    Call this before application shutdown to ensure all traces
    are properly recorded.
    """
    client = get_langfuse_client()
    if client:
        try:
            client.flush()
            llm_logger.info("Langfuse client flushed successfully")
        except Exception as e:
            llm_logger.error(f"Failed to flush Langfuse client: {e}")
