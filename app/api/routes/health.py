from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "hr-recruitment-backend"
    }


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HR AI Recruitment Manager API",
        "version": "0.1.0",
        "docs": "/docs"
    }
