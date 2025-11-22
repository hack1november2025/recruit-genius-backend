"""Schemas for CV model."""
from pydantic import BaseModel, Field
from datetime import datetime


class CVBase(BaseModel):
    """Base CV schema."""
    candidate_id: int


class CVCreate(CVBase):
    """Schema for creating a CV."""
    pass


class CVResponse(CVBase):
    """Schema for CV response."""
    id: int
    original_text: str
    translated_text: str | None
    original_language: str | None
    file_name: str | None
    file_path: str | None
    file_size_bytes: int | None
    extracted_name: str | None
    extracted_email: str | None
    extracted_phone: str | None
    structured_metadata: dict | None
    is_processed: bool
    is_translated: bool
    created_at: datetime
    updated_at: datetime | None
    
    class Config:
        from_attributes = True


class CVUploadRequest(BaseModel):
    """Request schema for CV upload."""
    candidate_id: int = Field(description="ID of the candidate")


class CVUploadResponse(BaseModel):
    """Response schema for CV upload."""
    success: bool
    cv_id: int | None = None
    candidate_id: int | None = None
    original_language: str | None = None
    metadata: dict | None = None
    error: str | None = None
