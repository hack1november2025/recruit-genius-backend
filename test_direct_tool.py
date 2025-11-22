"""Test save_job_to_database tool directly to diagnose the issue."""
import asyncio
from app.agents.job_generator.tools import save_job_to_database


async def test_save_job():
    """Test the save_job_to_database tool function directly."""
    print("🧪 Testing save_job_to_database tool directly...")
    print("")
    
    test_job = {
        "title": "Test Java Developer",
        "description": """# Test Java Developer

## About
Testing direct tool invocation.

## Responsibilities
- Test code
- Debug issues

## Requirements
- 3 years Java experience
- Problem solving skills

## Benefits
- Competitive salary
- Remote work
""",
        "department": "Engineering",
        "location": "Remote",
        "salary_range": "$80k-$120k"
    }
    
    try:
        print("Calling tool function directly with .coroutine()...")
        result = await save_job_to_database.coroutine(**test_job)
        print(f"✅ SUCCESS: {result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_save_job())
    exit(0 if success else 1)
