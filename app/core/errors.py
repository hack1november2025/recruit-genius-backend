"""Custom exceptions for the HR Recruitment Manager."""
from fastapi import HTTPException, status


class CVParsingError(Exception):
    """Raised when CV parsing fails."""
    pass


class EmbeddingGenerationError(Exception):
    """Raised when embedding generation fails."""
    pass


class RAGRetrievalError(Exception):
    """Raised when RAG retrieval fails."""
    pass


class LLMGenerationError(Exception):
    """Raised when LLM call fails."""
    pass


class FileUploadError(HTTPException):
    """Raised when file upload validation fails."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ResourceNotFoundError(HTTPException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, id: str | int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {id} not found"
        )


class MetricCalculationError(Exception):
    """Raised when metric calculation fails."""
    pass
