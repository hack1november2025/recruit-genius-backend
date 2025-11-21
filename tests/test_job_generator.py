"""Quick test for refactored conversational job generator."""
import asyncio
from app.services.job_generator import JobGeneratorService


async def test_conversational_flow():
    """Test the conversational job generator workflow."""
    
    service = JobGeneratorService()
    thread_id = "test_thread_123"
    
    print("=" * 60)
    print("TEST 1: Create Job Description")
    print("=" * 60)
    
    response1 = await service.chat(
        "Create a job posting for a senior Python developer with 5 years experience",
        thread_id
    )
    print(response1)
    print()
    
    print("=" * 60)
    print("TEST 2: Request Modification")
    print("=" * 60)
    
    response2 = await service.chat(
        "Make it more friendly and emphasize remote work",
        thread_id
    )
    print(response2)
    print()
    
    print("=" * 60)
    print("TEST 3: Save to Database")
    print("=" * 60)
    
    response3 = await service.chat(
        "Save this job with title 'Senior Python Developer', department 'Engineering', location 'Remote'",
        thread_id
    )
    print(response3)
    print()
    
    print("✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_conversational_flow())
