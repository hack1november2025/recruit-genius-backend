"""API routes for CV operations."""
import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.dependencies import get_db
from app.services.cv_processor import CVProcessorService
from app.services.cv_parser import CVParserService
from app.db.models.candidate import Candidate, CandidateStatus
from app.schemas.cv import CVUploadResponse, CVResponse
from app.repositories.cv import CVRepository
from app.core.logging import api_logger

router = APIRouter(prefix="/cvs", tags=["cvs"])


@router.post("/upload", response_model=CVUploadResponse)
async def upload_cv(
    file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a CV file.
    
    This endpoint:
    1. Receives a PDF or DOCX file
    2. Extracts basic info (email, name, phone) to find or create candidate
    3. Detects language and translates to English if needed
    4. Extracts structured metadata using LLM
    5. Creates embeddings for semantic search
    6. Stores everything in the database
    
    The candidate is automatically identified by email:
    - If email found in CV and candidate exists: link CV to existing candidate
    - If email found but no candidate exists: create new candidate
    - If no email found: create anonymous candidate
    
    Args:
        file: CV file to upload (PDF or DOCX)
        db: Database session
        
    Returns:
        Upload result with CV ID, candidate ID, and metadata
    """
    api_logger.info("Receiving CV upload")
    
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required"
        )
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
    
    # Save uploaded file to temporary location
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)
        
        api_logger.info(f"Saved uploaded file to {temp_path}")
        
        # Step 1: Extract basic info to identify/create candidate
        parser = CVParserService()
        basic_info = parser.parse_cv(temp_path)
        
        email = basic_info.get("email")
        name = basic_info.get("name")
        phone = basic_info.get("phone")
        
        api_logger.info(f"Extracted basic info - Email: {email}, Name: {name}")
        
        # Step 2: Find or create candidate
        candidate = None
        
        if email:
            # Try to find existing candidate by email
            result = await db.execute(
                select(Candidate).where(Candidate.email == email)
            )
            candidate = result.scalar_one_or_none()
            
            if candidate:
                api_logger.info(f"Found existing candidate {candidate.id} with email {email}")
            else:
                # Create new candidate
                candidate = Candidate(
                    name=name or f"Candidate_{email.split('@')[0]}",
                    email=email,
                    phone=phone,
                    status=CandidateStatus.NEW
                )
                db.add(candidate)
                await db.flush()
                await db.refresh(candidate)
                api_logger.info(f"Created new candidate {candidate.id} with email {email}")
        else:
            # No email found - create anonymous candidate
            import uuid
            anonymous_email = f"candidate_{uuid.uuid4().hex[:8]}@unknown.local"
            candidate = Candidate(
                name=name or f"Anonymous Candidate",
                email=anonymous_email,
                phone=phone,
                status=CandidateStatus.NEW
            )
            db.add(candidate)
            await db.flush()
            await db.refresh(candidate)
            api_logger.warning(f"No email found in CV, created anonymous candidate {candidate.id}")
        
        # Step 3: Process CV using the agent
        processor = CVProcessorService()
        result = await processor.process_cv(
            file_path=temp_path,
            candidate_id=candidate.id,
            db=db
        )
        
        # Clean up temporary file
        if temp_path and temp_path.exists():
            temp_path.unlink()
        
        if result["success"]:
            api_logger.info(f"Successfully processed CV {result['cv_id']} for candidate {candidate.id}")
            return CVUploadResponse(
                success=True,
                cv_id=result["cv_id"],
                candidate_id=candidate.id,
                original_language=result.get("original_language"),
                metadata=result.get("metadata")
            )
        else:
            api_logger.error(f"CV processing failed: {result.get('error')}")
            return CVUploadResponse(
                success=False,
                error=result.get("error")
            )
    
    except Exception as e:
        api_logger.error(f"CV upload failed: {str(e)}")
        # Clean up temp file if it exists
        if temp_path and temp_path.exists():
            temp_path.unlink()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CV processing failed: {str(e)}"
        )


@router.get("/candidate/{candidate_id}", response_model=list[CVResponse])
async def get_candidate_cvs(
    candidate_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all CVs for a specific candidate.
    
    Returns a list of all CVs associated with the candidate,
    ordered by creation date (most recent first).
    
    Args:
        candidate_id: ID of the candidate
        db: Database session
        
    Returns:
        List of CVs with all metadata
    """
    api_logger.info(f"Fetching CVs for candidate {candidate_id}")
    
    # Verify candidate exists
    result = await db.execute(
        select(Candidate).where(Candidate.id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Get all CVs for the candidate
    repo = CVRepository(db)
    cvs = await repo.get_by_candidate(candidate_id)
    
    api_logger.info(f"Found {len(cvs)} CVs for candidate {candidate_id}")
    return cvs
