from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.routes import health, candidates, jobs, matches, job_descriptions, cvs, matcher

settings = get_settings()

# Constants
API_V1_PREFIX = "/api/v1"

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered HR Recruitment Manager",
    version="0.1.0",
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=API_V1_PREFIX)
app.include_router(candidates.router, prefix=API_V1_PREFIX)
app.include_router(cvs.router, prefix=API_V1_PREFIX)  # New: CV upload and processing
app.include_router(job_descriptions.router, prefix=API_V1_PREFIX)  # New: AI job generation
app.include_router(jobs.router, prefix=API_V1_PREFIX)  # Standard CRUD
app.include_router(matches.router, prefix=API_V1_PREFIX)
app.include_router(matcher.router, prefix=API_V1_PREFIX)  # New: AI-powered job matching


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"🚀 Starting {settings.app_name}")
    print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"👋 Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
