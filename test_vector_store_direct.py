"""Direct test of vector store with async operations."""
import asyncio
from app.services.vector_store_service import get_vector_store_service


async def test_search():
    """Test similarity search directly."""
    
    print("Testing vector store async search...")
    
    vector_service = get_vector_store_service()
    
    try:
        results = await vector_service.similarity_search_with_score(
            query="Java developer",
            k=5
        )
        
        print(f"\n✅ Found {len(results)} results:")
        for doc, score in results:
            print(f"\n  Score: {score:.4f}")
            print(f"  Candidate: {doc.metadata.get('candidate_name', 'Unknown')}")
            print(f"  Preview: {doc.page_content[:100]}...")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_search())
