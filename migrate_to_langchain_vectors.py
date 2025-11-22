"""
Migration script to populate LangChain vector store from existing CV embeddings.

This script reads existing CV data and embeddings from the old schema (cv_embeddings table)
and populates the new LangChain PGVector tables for agentic RAG.
"""
import asyncio
from sqlalchemy import select
from langchain_core.documents import Document
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from app.db.session import AsyncSessionLocal
from app.db.models.cv import CV
from app.db.models.cv_embedding import CVEmbedding
from app.db.models.candidate import Candidate
from app.core.config import get_settings


async def migrate_cv_embeddings():
    """Migrate existing CV embeddings to LangChain vector store."""
    
    print("Starting migration of CV embeddings to LangChain vector store...")
    
    # Initialize embeddings and vector store (sync version)
    settings = get_settings()
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.openai_api_key
    )
    
    # Connection string for sync PGVector
    connection_string = settings.database_url.replace(
        "postgresql+asyncpg://",
        "postgresql+psycopg://"
    )
    
    # Create sync PGVector instance
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="cv_documents",
        connection=connection_string,
        use_jsonb=True,
    )
    
    async with AsyncSessionLocal() as db:
        # Get all processed CVs
        query = select(CV).where(CV.is_processed == True)
        result = await db.execute(query)
        cvs = result.scalars().all()
        
        print(f"Found {len(cvs)} processed CVs to migrate")
        
        total_chunks = 0
        
        for cv in cvs:
            try:
                # Get candidate info
                candidate_query = select(Candidate).where(Candidate.id == cv.candidate_id)
                candidate_result = await db.execute(candidate_query)
                candidate = candidate_result.scalar_one_or_none()
                
                if not candidate:
                    print(f"  Warning: CV {cv.id} has no candidate, skipping")
                    continue
                
                # Get embeddings for this CV
                embeddings_query = (
                    select(CVEmbedding)
                    .where(CVEmbedding.cv_id == cv.id)
                    .order_by(CVEmbedding.chunk_index)
                )
                embeddings_result = await db.execute(embeddings_query)
                emb_list = embeddings_result.scalars().all()
                
                if not emb_list:
                    print(f"  Warning: CV {cv.id} has no embeddings, skipping")
                    continue
                
                print(f"  Migrating CV {cv.id}: {candidate.name} ({len(emb_list)} chunks)")
                
                # Prepare metadata
                metadata = cv.structured_metadata or {}
                metadata.update({
                    "candidate_id": cv.candidate_id,
                    "candidate_name": candidate.name,
                    "candidate_email": candidate.email or "",
                    "cv_id": cv.id,
                    "original_language": cv.original_language or "en",
                    "skills": candidate.skills or [],
                    "experience_years": candidate.experience_years or 0,
                })
                
                # Create LangChain Document objects
                documents = [
                    Document(
                        page_content=emb.chunk_text,
                        metadata={
                            **metadata,
                            "chunk_index": emb.chunk_index,
                        }
                    )
                    for emb in emb_list
                ]
                
                # Add to LangChain vector store using sync method
                doc_ids = [f"cv_{cv.id}_chunk_{emb.chunk_index}" for emb in emb_list]
                vector_store.add_documents(documents, ids=doc_ids)
                
                total_chunks += len(emb_list)
                print(f"    ✓ Migrated {len(emb_list)} chunks")
                
            except Exception as e:
                print(f"  ✗ Error migrating CV {cv.id}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\nMigration complete!")
        print(f"  Total CVs migrated: {len(cvs)}")
        print(f"  Total chunks migrated: {total_chunks}")


if __name__ == "__main__":
    asyncio.run(migrate_cv_embeddings())
