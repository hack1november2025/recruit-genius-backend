"""Node functions for CV Parser agent."""
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.cv_parser.state import CVParserState
from app.services.cv_parser import CVParserService
from app.services.translation_service import TranslationService
from app.services.metadata_extraction_service import MetadataExtractionService
from app.services.embedding_service import EmbeddingService
from app.db.models.cv import CV
from app.db.models.cv_embedding import CVEmbedding
from app.core.logging import llm_logger


def extract_text_node(state: CVParserState) -> dict:
    """Extract text from PDF/DOCX file."""
    llm_logger.info(f"Extracting text from: {state['file_path']}")
    
    try:
        parser = CVParserService()
        file_path = Path(state["file_path"])
        
        # Extract text and basic info
        parsed_data = parser.parse_cv(file_path)
        
        return {
            "raw_text": parsed_data["resume_text"],
            "status": "processing"
        }
    except Exception as e:
        llm_logger.error(f"Text extraction failed: {str(e)}")
        return {
            "error": f"Text extraction failed: {str(e)}",
            "status": "failed"
        }


async def detect_and_translate_node(state: CVParserState) -> dict:
    """Detect language and translate to English if needed."""
    llm_logger.info("Detecting language and translating if needed")
    
    if not state.get("raw_text"):
        return {
            "error": "No text to translate",
            "status": "failed"
        }
    
    try:
        translation_service = TranslationService()
        
        result = await translation_service.translate_to_english(state["raw_text"])
        
        return {
            "original_language": result["original_language"],
            "translated_text": result["translated_text"],
            "status": "processing"
        }
    except Exception as e:
        llm_logger.error(f"Translation failed: {str(e)}")
        # Continue with original text if translation fails
        return {
            "original_language": "unknown",
            "translated_text": state["raw_text"],
            "status": "processing"
        }


async def extract_metadata_node(state: CVParserState) -> dict:
    """Extract structured metadata from CV text."""
    llm_logger.info("Extracting structured metadata")
    
    if not state.get("translated_text"):
        return {
            "error": "No translated text available",
            "status": "failed"
        }
    
    try:
        metadata_service = MetadataExtractionService()
        
        metadata = await metadata_service.extract_metadata(state["translated_text"])
        
        return {
            "structured_metadata": metadata,
            "status": "processing"
        }
    except Exception as e:
        llm_logger.error(f"Metadata extraction failed: {str(e)}")
        return {
            "error": f"Metadata extraction failed: {str(e)}",
            "status": "failed"
        }


async def create_embeddings_node(state: CVParserState, db: AsyncSession) -> dict:
    """Create embeddings for CV text and store in database + LangChain vector store."""
    llm_logger.info("Creating embeddings for CV")
    
    if not state.get("translated_text"):
        return {
            "error": "No translated text for embeddings",
            "status": "failed"
        }
    
    try:
        from langchain_core.documents import Document
        from app.services.vector_store_service import get_vector_store_service
        
        embedding_service = EmbeddingService()
        
        # First, create CV record in database
        file_path = Path(state["file_path"])
        cv = CV(
            candidate_id=state["candidate_id"],
            original_text=state.get("raw_text", ""),
            translated_text=state["translated_text"],
            original_language=state.get("original_language"),
            file_name=file_path.name,
            file_path=str(file_path),
            file_size_bytes=file_path.stat().st_size if file_path.exists() else None,
            structured_metadata=state.get("structured_metadata"),
            is_processed=False,
            is_translated=state.get("original_language") != "en"
        )
        
        db.add(cv)
        await db.flush()
        await db.refresh(cv)
        
        # Get candidate info for metadata
        from app.db.models.candidate import Candidate
        from sqlalchemy import select
        candidate_query = select(Candidate).where(Candidate.id == state["candidate_id"])
        candidate_result = await db.execute(candidate_query)
        candidate = candidate_result.scalar_one_or_none()
        
        # Chunk and embed the translated text
        chunks = embedding_service.chunk_text(state["translated_text"], chunk_size=500, overlap=50)
        embeddings = await embedding_service.generate_embeddings(chunks)
        
        # Store embeddings in OLD schema (cv_embeddings table) for backward compatibility
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            cv_embedding = CVEmbedding(
                cv_id=cv.id,
                chunk_index=idx,
                chunk_text=chunk,
                embedding=embedding,
                embedding_metadata={"source": "cv_parser_agent"}
            )
            db.add(cv_embedding)
        
        # Also store in LangChain PGVector (NEW schema) for agentic RAG
        llm_logger.info(f"Storing {len(chunks)} chunks in LangChain vector store")
        
        # Create metadata for LangChain documents
        metadata = state.get("structured_metadata", {})
        metadata.update({
            "candidate_id": state["candidate_id"],
            "candidate_name": candidate.name if candidate else "Unknown",
            "candidate_email": candidate.email if candidate else "Unknown",
            "cv_id": cv.id,
            "original_language": state.get("original_language"),
        })
        
        # Create LangChain Document objects
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    **metadata,
                    "chunk_index": idx,
                    "custom_id": f"cv_{cv.id}_chunk_{idx}"
                }
            )
            for idx, chunk in enumerate(chunks)
        ]
        
        # Add to LangChain vector store
        vector_store_service = get_vector_store_service()
        doc_ids = [f"cv_{cv.id}_chunk_{idx}" for idx in range(len(chunks))]
        await vector_store_service.add_documents(documents, ids=doc_ids)
        
        # Mark CV as processed
        cv.is_processed = True
        
        # Commit is handled by the caller (cv_processor service)
        # Don't commit here to allow caller to handle transaction
        
        llm_logger.info(f"Created {len(chunks)} embeddings for CV {cv.id} in both schemas")
        
        return {
            "cv_id": cv.id,
            "embeddings_created": True,
            "status": "completed"
        }
    except Exception as e:
        llm_logger.error(f"Embedding creation failed: {str(e)}")
        raise  # Re-raise to allow caller to handle rollback
