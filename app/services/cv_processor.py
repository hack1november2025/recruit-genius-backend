"""Service for CV processing using CV Parser agent."""
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.cv_parser.graph import create_cv_parser_graph
from app.agents.cv_parser.state import CVParserState
from app.core.logging import llm_logger


class CVProcessorService:
    """Service for processing CV uploads using the CV Parser agent."""
    
    async def process_cv(
        self,
        file_path: str | Path,
        candidate_id: int,
        db: AsyncSession
    ) -> dict:
        """
        Process an uploaded CV file.
        
        Args:
            file_path: Path to the uploaded CV file
            candidate_id: ID of the candidate this CV belongs to
            db: Database session
            
        Returns:
            Dictionary with processing results
        """
        llm_logger.info(f"Processing CV for candidate {candidate_id}")
        
        # Create graph with database session
        graph = create_cv_parser_graph(db)
        
        # Prepare initial state
        initial_state: CVParserState = {
            "file_path": str(file_path),
            "candidate_id": candidate_id,
            "raw_text": None,
            "original_language": None,
            "translated_text": None,
            "structured_metadata": None,
            "embeddings_created": False,
            "cv_id": None,
            "error": None,
            "status": "pending"
        }
        
        try:
            # Execute agent workflow
            result = await graph.ainvoke(initial_state)
            
            if result["status"] == "completed":
                # Commit the transaction
                await db.commit()
                llm_logger.info(f"Successfully processed CV {result['cv_id']}")
                return {
                    "success": True,
                    "cv_id": result["cv_id"],
                    "original_language": result["original_language"],
                    "metadata": result["structured_metadata"]
                }
            else:
                # Rollback on failure
                await db.rollback()
                llm_logger.error(f"CV processing failed: {result.get('error')}")
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
        
        except Exception as e:
            # Rollback on exception
            await db.rollback()
            llm_logger.error(f"CV processing exception: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
