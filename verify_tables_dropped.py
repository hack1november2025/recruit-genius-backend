"""Verify old tables are dropped."""
import asyncio
from sqlalchemy import text
from app.db.session import AsyncSessionLocal


async def verify_tables():
    """Check which embedding tables exist."""
    
    print("Checking database tables...\n")
    
    async with AsyncSessionLocal() as db:
        # Check for old tables
        result = await db.execute(
            text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%embedding%'
                ORDER BY table_name
            """)
        )
        tables = result.fetchall()
        
        print("Embedding-related tables:")
        for table in tables:
            print(f"  - {table.table_name}")
        
        # Check if old tables exist
        old_tables = [t.table_name for t in tables if t.table_name in ('cv_embeddings', 'job_embeddings')]
        
        if old_tables:
            print(f"\n❌ Old tables still exist: {', '.join(old_tables)}")
        else:
            print("\n✅ Old embedding tables successfully dropped!")
        
        # Check new tables exist
        new_tables = [t.table_name for t in tables if t.table_name in ('langchain_pg_embedding',)]
        
        if new_tables:
            print(f"✅ New LangChain tables exist: {', '.join(new_tables)}")
        else:
            print("❌ New LangChain tables missing!")


if __name__ == "__main__":
    asyncio.run(verify_tables())
