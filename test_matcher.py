"""
Test script for the matcher agent.

This script tests the end-to-end matching workflow.
Requires:
- A running PostgreSQL database with data
- At least one job with embeddings and metadata
- At least one candidate/CV with embeddings and metadata
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.services.matcher import MatcherService
from app.core.logging import rag_logger
import json


async def test_matcher():
    """Test the matcher service."""
    
    async with AsyncSessionLocal() as db:
        matcher_service = MatcherService(db)
        
        # Test with job_id = 1 (adjust as needed)
        job_id = 1
        top_k = 5
        
        print(f"\n{'='*80}")
        print(f"Testing Matcher Agent for Job ID: {job_id}")
        print(f"{'='*80}\n")
        
        try:
            result = await matcher_service.find_matches_for_job(
                job_id=job_id,
                top_k=top_k,
                hard_constraints_overrides={},
                persist_matches=False  # Don't persist during testing
            )
            
            if result.get("error"):
                print(f"❌ Error: {result['error']}")
                return
            
            # Print summary
            summary = result.get("summary", {})
            print("📋 JOB SUMMARY:")
            print(f"  Title: {summary.get('role_title', 'N/A')}")
            print(f"  Stack: {summary.get('primary_stack_or_domain', 'N/A')}")
            print(f"  Required Skills: {', '.join(summary.get('key_required_skills', [])[:5])}")
            print(f"  Nice-to-have: {', '.join(summary.get('nice_to_have_skills', [])[:5])}")
            print(f"\n🔍 CONSTRAINTS APPLIED:")
            for constraint in summary.get('hard_constraints_applied', []):
                print(f"  - {constraint}")
            
            # Print candidates
            candidates = result.get("candidates", [])
            print(f"\n👥 FOUND {len(candidates)} MATCHING CANDIDATES:\n")
            
            for i, candidate in enumerate(candidates, 1):
                print(f"{i}. {candidate['name']} (ID: {candidate['candidate_id']})")
                print(f"   Current Role: {candidate['current_role']}")
                print(f"   Match Score: {candidate['match_score']:.1f}/100")
                print(f"   Semantic Similarity: {candidate['hybrid_similarity_score']:.3f}")
                print(f"   Seniority: {candidate['seniority_match']}")
                print(f"   Experience: {candidate['experience']['total_years_experience']} years")
                print(f"   Matched Skills: {', '.join(candidate['matched_skills'][:5])}")
                if candidate['missing_required_skills']:
                    print(f"   Missing Skills: {', '.join(candidate['missing_required_skills'][:3])}")
                print(f"   Rationale: {candidate['overall_rationale'][:150]}...")
                print()
            
            # Save results to file
            with open("matcher_test_results.json", "w") as f:
                json.dump(result, f, indent=2)
            print("✅ Full results saved to matcher_test_results.json")
            
        except Exception as e:
            rag_logger.error(f"Test failed: {str(e)}")
            print(f"❌ Test failed: {str(e)}")
            raise


async def test_specific_job(job_id: int):
    """Test matcher with a specific job ID."""
    
    async with AsyncSessionLocal() as db:
        matcher_service = MatcherService(db)
        
        print(f"\n{'='*80}")
        print(f"Testing Matcher for Job ID: {job_id}")
        print(f"{'='*80}\n")
        
        result = await matcher_service.find_matches_for_job(
            job_id=job_id,
            top_k=10,
            persist_matches=False
        )
        
        if result.get("error"):
            print(f"❌ Error: {result['error']}")
        else:
            print(f"✅ Found {len(result.get('candidates', []))} matches")
            print(f"📊 Summary: {result.get('summary', {})}")


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_matcher())
    
    # To test a specific job:
    # asyncio.run(test_specific_job(1))
