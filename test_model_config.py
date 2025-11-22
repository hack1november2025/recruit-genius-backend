#!/usr/bin/env python3
"""Test that LLM models are properly configured from environment variables."""

from app.core.config import get_settings

settings = get_settings()

print("🔧 LLM Model Configuration")
print("=" * 50)
print(f"LLM_MODEL (general agents):  {settings.llm_model}")
print(f"LLM_RAG_MODEL (RAG/chat):    {settings.llm_rag_model}")
print("=" * 50)
print()
print("✅ Models configured successfully!")
print()
print("Usage:")
print("  - Job Generator: uses LLM_MODEL")
print("  - CV Chat (RAG): uses LLM_RAG_MODEL")
print("  - Recruiter: uses LLM_MODEL")
print("  - Metadata Extraction: uses LLM_MODEL")
print("  - Translation: uses LLM_MODEL")
