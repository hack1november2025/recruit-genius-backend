"""Test script for job processing - embeddings and metadata generation."""
import asyncio
from sqlalchemy import select, func
from app.db.session import AsyncSessionLocal
from app.db.models.job import Job
from app.db.models.job_embedding import JobEmbedding
from app.db.models.job_metadata import JobMetadata
from app.services.job_processing_service import JobProcessingService


async def check_processing_status():
    """Check the current state of job processing."""
    async with AsyncSessionLocal() as db:
        # Count jobs
        result = await db.execute(select(func.count(Job.id)))
        total_jobs = result.scalar()
        
        # Count embeddings
        result = await db.execute(select(func.count(JobEmbedding.id)))
        total_embeddings = result.scalar()
        
        # Count metadata
        result = await db.execute(select(func.count(JobMetadata.id)))
        total_metadata = result.scalar()
        
        print("\n" + "="*60)
        print("📊 JOB PROCESSING STATUS")
        print("="*60)
        print(f"Total Jobs: {total_jobs}")
        print(f"Total Embeddings: {total_embeddings}")
        print(f"Total Metadata Records: {total_metadata}")
        print()
        
        # Check which jobs need processing
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        
        if not jobs:
            print("⚠️  No jobs found in database")
            return
        
        print("Job Processing Details:")
        print("-" * 60)
        
        for job in jobs:
            # Check embeddings
            result = await db.execute(
                select(func.count(JobEmbedding.id)).where(JobEmbedding.job_id == job.id)
            )
            job_embeddings = result.scalar()
            
            # Check metadata
            result = await db.execute(
                select(func.count(JobMetadata.id)).where(JobMetadata.job_id == job.id)
            )
            job_metadata = result.scalar()
            
            status = "✅" if (job_embeddings > 0 and job_metadata > 0) else "❌"
            print(f"{status} Job #{job.id}: {job.title[:50]}")
            print(f"   Embeddings: {job_embeddings} | Metadata: {job_metadata}")
        
        print("="*60 + "\n")


async def reprocess_all_jobs():
    """Reprocess all jobs to generate embeddings and metadata."""
    processing_service = JobProcessingService()
    
    async with AsyncSessionLocal() as db:
        # Get all jobs
        result = await db.execute(select(Job))
        jobs = result.scalars().all()
        
        if not jobs:
            print("⚠️  No jobs to process")
            return
        
        print(f"\n🔄 Processing {len(jobs)} jobs...\n")
        
        processed = 0
        failed = 0
        
        for job in jobs:
            print(f"Processing Job #{job.id}: {job.title[:50]}...")
            
            try:
                result = await processing_service.process_job_description(
                    job_id=job.id,
                    job_description=job.description,
                    db=db
                )
                
                if result.get("success"):
                    embeddings_count = result.get("embeddings_count", 0)
                    print(f"  ✅ Success! {embeddings_count} embeddings created")
                    processed += 1
                else:
                    print(f"  ❌ Failed: {result.get('error')}")
                    failed += 1
            
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                failed += 1
        
        print(f"\n📈 Results: {processed} processed, {failed} failed\n")


async def main():
    """Main test function."""
    print("\n" + "="*60)
    print("🧪 JOB PROCESSING TEST SCRIPT")
    print("="*60)
    
    # Check current status
    await check_processing_status()
    
    # Ask to reprocess
    print("Would you like to reprocess all jobs? (y/n): ", end="")
    import sys
    response = sys.stdin.readline().strip().lower()
    
    if response == 'y':
        await reprocess_all_jobs()
        print("\n✅ Reprocessing complete!\n")
        
        # Show updated status
        await check_processing_status()
    else:
        print("\nℹ️  Skipping reprocessing. Run with 'y' to process jobs.\n")
        print("💡 You can also use the API endpoint:")
        print("   POST /api/v1/jobs/batch-reprocess")
        print("   POST /api/v1/jobs/{job_id}/reprocess\n")


if __name__ == "__main__":
    asyncio.run(main())
