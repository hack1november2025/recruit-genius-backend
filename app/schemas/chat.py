"""Pydantic schemas for chat functionality."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ChatQueryRequest(BaseModel):
    """Schema for sending a chat query."""
    query: str = Field(..., min_length=1, max_length=2000)
    thread_id: str | None = None  # Optional - will be generated if not provided
    user_identifier: str = Field(default="web_user")


class CandidateSummary(BaseModel):
    """Schema for candidate summary in chat response."""
    candidate_id: int
    name: str
    email: str
    skills: List[str] = Field(default_factory=list)
    experience_years: float | None = None
    location: str | None = None
    similarity_score: float | None = None
    summary: str | None = None


class ChatQueryResponse(BaseModel):
    """Schema for chat query response."""
    thread_id: str
    response_text: str
    structured_response: Dict[str, Any]
    candidate_ids: List[int] = Field(default_factory=list)
    error: str | None = None


class TelegramChatRequest(BaseModel):
    """Schema for Telegram bot chat request."""
    telegram_user_id: str
    message: str
    thread_id: str | None = None


class TelegramChatResponse(BaseModel):
    """Schema for Telegram bot chat response."""
    thread_id: str
    response_text: str
    candidates: List[CandidateSummary] = Field(default_factory=list)
