"""Verify LangChain vector store migration."""
import asyncio
from sqlalchemy import select, func, text
from app.db.session import AsyncSessionLocal


async def verify_migration():
    """Verify the LangChain tables are populated."""
    
    print("Verifying LangChain vector store migration...\n")
    
    async with AsyncSessionLocal() as db:
        # Check langchain_pg_collection
        result = await db.execute(
            text("SELECT uuid, name FROM langchain_pg_collection")
        )
        collections = result.fetchall()
        
        print(f"Collections in langchain_pg_collection:")
        for col in collections:
            print(f"  - {col.name} (UUID: {col.uuid})")
        
        # Check langchain_pg_embedding count
        result = await db.execute(
            text("SELECT COUNT(*) as count FROM langchain_pg_embedding")
        )
        count = result.scalar()
        
        print(f"\nTotal documents in langchain_pg_embedding: {count}")
        
        # Sample some documents
        result = await db.execute(
            text("""
                SELECT 
                    id,
                    LEFT(document, 100) as doc_preview,
                    cmetadata->>'candidate_name' as candidate_name,
                    cmetadata->>'chunk_index' as chunk_index
                FROM langchain_pg_embedding
                LIMIT 5
            """)
        )
        docs = result.fetchall()
        
        print(f"\nSample documents:")
        for doc in docs:
            print(f"  ID: {doc.id}")
            print(f"  Candidate: {doc.candidate_name}")
            print(f"  Chunk: {doc.chunk_index}")
            print(f"  Preview: {doc.doc_preview}...")
            print()


if __name__ == "__main__":
    asyncio.run(verify_migration())
