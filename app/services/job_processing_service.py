"""Service for processing job descriptions with embeddings and metadata using LangChain."""
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.documents import Document
from app.services.vector_store_service import VectorStoreService
from app.services.embedding_service import EmbeddingService
from app.services.job_metadata_extraction_service import JobMetadataExtractionService
from app.db.models.job_metadata import JobMetadata
from app.core.logging import llm_logger


class JobProcessingService:
    """Service for processing job descriptions: embeddings + metadata extraction using LangChain."""
    
    def __init__(self):
        self.vector_store_service = VectorStoreService()
        self.embedding_service = EmbeddingService()
        self.metadata_service = JobMetadataExtractionService()
    
    async def process_job_description(
        self,
        job_id: int,
        job_description: str,
        db: AsyncSession
    ) -> dict:
        """
        Process a job description: create embeddings and extract metadata.
        
        Args:
            job_id: ID of the job
            job_description: Full job description text
            db: Database session
            
        Returns:
            Dictionary with processing results
        """
        llm_logger.info(f"Processing job description for job {job_id}")
        
        try:
            # Extract metadata using LLM
            llm_logger.info("Extracting job metadata")
            metadata_dict = await self.metadata_service.extract_job_metadata(job_description)
            
            # Create job metadata record
            job_metadata = JobMetadata(
                job_id=job_id,
                required_skills=metadata_dict.get("required_skills", []),
                preferred_skills=metadata_dict.get("preferred_skills", []),
                min_experience_years=metadata_dict.get("min_experience_years"),
                max_experience_years=metadata_dict.get("max_experience_years"),
                required_education=metadata_dict.get("required_education"),
                preferred_education=metadata_dict.get("preferred_education"),
                remote_type=metadata_dict.get("remote_type"),
                locations=metadata_dict.get("locations", []),
                seniority_level=metadata_dict.get("seniority_level"),
                role_type=metadata_dict.get("role_type"),
                min_salary=metadata_dict.get("min_salary"),
                max_salary=metadata_dict.get("max_salary"),
                currency=metadata_dict.get("currency", "USD"),
                required_certifications=metadata_dict.get("required_certifications", []),
                preferred_certifications=metadata_dict.get("preferred_certifications", []),
                responsibilities=metadata_dict.get("responsibilities", []),
                benefits=metadata_dict.get("benefits", []),
                tech_stack=metadata_dict.get("tech_stack", []),
                full_metadata=metadata_dict
            )
            db.add(job_metadata)
            
            # Create embeddings using LangChain vector store
            llm_logger.info("Creating job description embeddings")
            chunks = self.embedding_service.chunk_text(job_description, chunk_size=500, overlap=50)
            
            # Create LangChain Documents with metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "job_id": job_id,
                        "chunk_index": idx,
                        "source": "job_processing_service",
                        "entity_type": "job",
                        "title": metadata_dict.get("title", ""),
                        "required_skills": metadata_dict.get("required_skills", [])[:5],  # First 5 skills
                        "seniority_level": metadata_dict.get("seniority_level", ""),
                    }
                )
                for idx, chunk in enumerate(chunks)
            ]
            
            # Store in LangChain vector store (runs in thread pool)
            import asyncio
            vector_store = self.vector_store_service.get_vector_store()
            await asyncio.to_thread(
                vector_store.add_documents,
                documents,
                ids=[f"job_{job_id}_chunk_{idx}" for idx in range(len(chunks))]
            )
            
            await db.commit()
            
            llm_logger.info(f"Successfully processed job {job_id}: {len(chunks)} embeddings created")
            
            return {
                "success": True,
                "embeddings_count": len(chunks),
                "metadata": metadata_dict
            }
        
        except Exception as e:
            llm_logger.error(f"Job processing failed: {str(e)}")
            await db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
