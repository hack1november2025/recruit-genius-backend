"""Tools for CV Chat agent - RAG retrieval using LangChain tool pattern."""
from typing import List, Annotated
from langchain_core.tools import tool
from app.services.vector_store_service import get_vector_store_service
from app.core.logging import rag_logger


@tool
async def search_candidates(
    query: Annotated[str, "Natural language search query to find candidates"],
    top_k: Annotated[int, "Maximum number of results to return"] = 10,
) -> str:
    """
    Search for candidates using semantic search over their CVs.
    
    This tool performs vector similarity search to find candidates whose CVs
    best match the natural language query. Use this when the user asks to:
    - Find candidates with specific skills (e.g. "Java developers", "Python engineers")
    - Search for candidates matching a job description  
    - Look for candidates with certain experience or background
    - Discover candidates in a particular domain or technology
    
    Args:
        query: Natural language description of what you're looking for
        top_k: Maximum number of candidates to return (default: 10)
        
    Returns:
        JSON-formatted string containing candidate information with similarity scores
    """
    try:
        rag_logger.info(f"RAG Tool: Searching candidates with query='{query}', top_k={top_k}")
        
        # Get vector store service (uses LangChain's PGVector)
        vector_store_service = get_vector_store_service()
        
        # Perform similarity search with scores
        results = await vector_store_service.similarity_search_with_score(
            query=query,
            k=top_k
        )
        
        if not results:
            rag_logger.info("No candidates found matching the query")
            return "No candidates found matching your search criteria. Try using different keywords or less specific requirements."
        
        # Format results for LLM
        # Each Document has page_content (CV text) and metadata (candidate info)
        candidates_info = []
        for doc, score in results:
            metadata = doc.metadata
            
            candidate_info = {
                "candidate_id": metadata.get("candidate_id"),
                "name": metadata.get("candidate_name"),
                "email": metadata.get("candidate_email"),
                "similarity_score": round(float(score), 3),
                "skills": metadata.get("skills", []),
                "experience_years": metadata.get("experience_years"),
                "education": metadata.get("education", []),
                "job_titles": metadata.get("job_titles", []),
                "companies": metadata.get("companies", []),
                "location": metadata.get("location"),
                "summary": metadata.get("summary", "")[:300],  # Limit summary length
                "cv_snippet": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            }
            candidates_info.append(candidate_info)
        
        rag_logger.info(f"RAG Tool: Found {len(candidates_info)} candidates")
        
        # Return formatted results as string for LLM
        import json
        return json.dumps({
            "total_found": len(candidates_info),
            "candidates": candidates_info,
            "message": f"Found {len(candidates_info)} candidate(s) matching your criteria"
        }, indent=2)
        
    except Exception as e:
        rag_logger.error(f"Error in search_candidates tool: {str(e)}", exc_info=True)
        return f"Error searching candidates: {str(e)}"


# Helper function to create tool list for agent
def get_cv_chat_tools() -> List:
    """
    Get list of tools for CV chat agent.
    
    Returns:
        List of LangChain tool instances
    """
    return [
        search_candidates,
    ]
