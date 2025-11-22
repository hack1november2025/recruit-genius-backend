"""Node functions for CV Chat agent workflow."""
import json
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.agents.cv_chat.state import CVChatState
from app.agents.cv_chat.tools import (
    search_candidates_by_query,
    get_candidate_details,
    compare_candidates,
    filter_candidates_by_criteria
)
from app.core.config import get_settings
from app.core.logging import rag_logger


# System prompt for the CV chat agent
SYSTEM_PROMPT = """You are an expert HR assistant with access to a comprehensive CV database. 
Your role is to help HR personnel find, filter, and analyze candidate profiles using natural language.

Capabilities:
- Search for candidates based on skills, experience, location, education, job titles, companies
- Filter and refine search results based on multiple criteria
- Compare candidates side-by-side
- Provide detailed information about specific candidates
- Answer questions about candidate qualifications and experience

Guidelines:
- Be concise and professional in your responses
- Always provide relevant candidate information when available
- If a query is ambiguous, ask for clarification
- When presenting multiple candidates, summarize key qualifications
- Use the conversation history to maintain context across multiple turns
- If no candidates match the criteria, suggest alternative search approaches

Current conversation context will be provided in the message history.
"""


async def understand_query_node(state: CVChatState, db: AsyncSession) -> dict:
    """
    Analyze the user query to understand intent and extract search parameters.
    
    This node:
    1. Analyzes the user's natural language query
    2. Determines the intent (search, filter, compare, detail, clarify)
    3. Extracts structured search parameters
    4. Identifies if clarification is needed
    
    Args:
        state: Current agent state
        db: Database session (unused but required by graph signature)
        
    Returns:
        Updated state with query intent and search parameters
    """
    try:
        rag_logger.info(f"Understanding query: {state['user_query'][:100]}")
        
        settings = get_settings()
        llm = ChatOpenAI(
            model=settings.llm_rag_model,
            temperature=0,
            openai_api_key=settings.openai_api_key,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        # Build prompt for query understanding
        analysis_prompt = f"""Analyze this HR candidate search query and extract structured information.

User Query: {state['user_query']}

Determine:
1. Intent: search (find new candidates), filter (refine existing results), compare (compare specific candidates), 
   detail (get info about one candidate), clarify (query is COMPLETELY UNCLEAR or empty)
2. Search parameters: skills, min_experience_years, location, companies, job_titles, education
3. Whether clarification is needed

IMPORTANT RULES:
- Simple queries like "java developer", "python engineer", "data scientist" are VALID searches - DO NOT require clarification
- Only set requires_clarification=true if the query is EXTREMELY vague (e.g., "find someone", "show me people") or empty
- If you can extract ANY search parameters (skills, job titles, etc.), set requires_clarification=false
- Err on the side of searching rather than asking for clarification

Respond in JSON format:
{{
    "intent": "search|filter|compare|detail|clarify",
    "search_params": {{
        "skills": ["skill1", "skill2"],
        "min_experience_years": 5,
        "location": "London",
        "companies": ["company1"],
        "job_titles": ["title1"]
    }},
    "requires_clarification": false,
    "clarification_message": "What specific skills are you looking for?"
}}

If the query references "them", "these candidates", or similar, set intent to "filter".
If comparing specific candidates, set intent to "compare".
"""
        
        response = await llm.ainvoke([
            SystemMessage(content="You are a query analysis expert. Respond only with valid JSON."),
            HumanMessage(content=analysis_prompt)
        ])
        
        # Parse the response - handle potential non-JSON responses
        try:
            # Try to extract JSON from response (might be wrapped in markdown code blocks)
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            elif content.startswith("```"):
                content = content[3:]  # Remove ```
            
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            analysis_result = json.loads(content)
            rag_logger.info(f"Query intent: {analysis_result['intent']}")
        except json.JSONDecodeError as e:
            rag_logger.warning(f"Failed to parse JSON response: {e}. Response: {response.content[:200]}")
            # Fallback: treat as general search query
            analysis_result = {
                "intent": "search",
                "search_params": {},
                "requires_clarification": False
            }
            rag_logger.info("Using fallback intent: search")
        
        return {
            "query_intent": analysis_result["intent"],
            "search_params": analysis_result.get("search_params", {}),
            "requires_clarification": analysis_result.get("requires_clarification", False),
            "clarification_message": analysis_result.get("clarification_message"),
        }
        
    except Exception as e:
        rag_logger.error(f"Error understanding query: {str(e)}")
        return {
            "error": f"Failed to understand query: {str(e)}",
            "query_intent": "clarify",
            "requires_clarification": True,
            "clarification_message": "I didn't quite understand that. Could you rephrase your question?"
        }


async def retrieve_candidates_node(state: CVChatState, db: AsyncSession) -> dict:
    """
    Retrieve candidates based on the query intent and parameters.
    
    Handles different intents:
    - search: Perform new RAG search
    - filter: Apply filters to existing results
    - compare: Get details for specific candidates
    - detail: Get detailed info about one candidate
    
    Args:
        state: Current agent state
        db: Database session
        
    Returns:
        Updated state with candidate results
    """
    try:
        intent = state["query_intent"]
        rag_logger.info(f"Retrieving candidates for intent: {intent}")
        rag_logger.info(f"User query: {state.get('user_query', 'N/A')[:100]}")
        rag_logger.info(f"Search params: {state.get('search_params', {})}")
        
        candidates = []
        
        if intent == "search":
            # Perform new RAG search
            rag_logger.info(f"Performing RAG search with query: {state['user_query'][:100]}")
            candidates = await search_candidates_by_query(
                db=db,
                query_text=state["user_query"],
                top_k=20,
                similarity_threshold=0.3
            )
            rag_logger.info(f"RAG search returned {len(candidates)} candidates")
            
        elif intent == "filter":
            # Filter existing candidates from context
            if state.get("candidate_ids_in_context"):
                candidates = await filter_candidates_by_criteria(
                    db=db,
                    base_candidate_ids=state["candidate_ids_in_context"],
                    criteria=state["search_params"]
                )
            else:
                # No context, perform new search
                candidates = await search_candidates_by_query(
                    db=db,
                    query_text=state["user_query"],
                    top_k=20,
                    similarity_threshold=0.3
                )
        
        elif intent == "compare":
            # Get details for comparison
            if state.get("candidate_ids_in_context"):
                candidates = await compare_candidates(
                    db=db,
                    candidate_ids=state["candidate_ids_in_context"]
                )
        
        elif intent == "detail":
            # Get detailed info about a specific candidate
            if state.get("candidate_ids_in_context"):
                candidate_id = state["candidate_ids_in_context"][0]
                detail = await get_candidate_details(db, candidate_id)
                if detail:
                    candidates = [detail]
        
        # Update context with new candidate IDs
        candidate_ids = [c["candidate_id"] for c in candidates]
        
        rag_logger.info(f"Retrieved {len(candidates)} candidates")
        
        return {
            "candidate_results": candidates,
            "candidate_ids_in_context": candidate_ids
        }
        
    except Exception as e:
        rag_logger.error(f"Error retrieving candidates: {str(e)}")
        return {
            "error": f"Failed to retrieve candidates: {str(e)}",
            "candidate_results": []
        }


async def generate_response_node(state: CVChatState, db: AsyncSession) -> dict:
    """
    Generate natural language response based on retrieved candidates and conversation history.
    
    This node:
    1. Takes the retrieved candidates
    2. Considers conversation history
    3. Generates a helpful, contextual response
    4. Creates structured data for UI rendering
    
    Args:
        state: Current agent state
        db: Database session (unused but required by graph signature)
        
    Returns:
        Updated state with response text and structured response
    """
    try:
        # If clarification needed, return clarification message
        if state.get("requires_clarification"):
            return {
                "response_text": state["clarification_message"],
                "structured_response": {
                    "type": "clarification",
                    "message": state["clarification_message"]
                }
            }
        
        # If error occurred, return error message
        if state.get("error"):
            return {
                "response_text": "I encountered an error processing your request. Please try rephrasing your question.",
                "structured_response": {
                    "type": "error",
                    "message": state["error"]
                }
            }
        
        candidates = state["candidate_results"]
        rag_logger.info(f"Generating response for {len(candidates)} candidates")
        
        settings = get_settings()
        llm = ChatOpenAI(
            model=settings.llm_rag_model,
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Prepare candidate data for the LLM
        candidates_summary = []
        for i, candidate in enumerate(candidates[:10], 1):  # Limit to top 10 for response
            summary = {
                "id": candidate["candidate_id"],
                "name": candidate["candidate_name"],
                "email": candidate["candidate_email"],
                "skills": candidate.get("skills", [])[:10],  # Top 10 skills
                "experience_years": candidate.get("experience_years"),
                "location": candidate.get("location"),
                "companies": candidate.get("companies", [])[:3],  # Top 3 companies
                "job_titles": candidate.get("job_titles", [])[:3],  # Top 3 titles
            }
            candidates_summary.append(summary)
        
        # Build prompt with conversation history
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],  # Include conversation history
        ]
        
        # Add current query and results
        results_text = f"""User query: {state['user_query']}

Retrieved {len(candidates)} candidates. Top results:
{json.dumps(candidates_summary, indent=2)}

Generate a helpful, professional response that:
1. Directly answers the user's question
2. Summarizes the most relevant candidates (if any)
3. Highlights key qualifications that match the query
4. Suggests next steps or follow-up questions if appropriate
5. If no candidates found, suggest alternative search criteria

Keep the response concise but informative."""
        
        messages.append(HumanMessage(content=results_text))
        
        response = await llm.ainvoke(messages)
        response_text = response.content
        
        # Create structured response for UI
        structured_response = {
            "type": "candidates" if candidates else "no_results",
            "message": response_text,
            "candidates": [
                {
                    "candidate_id": c["candidate_id"],
                    "name": c["candidate_name"],
                    "email": c["candidate_email"],
                    "skills": c.get("skills", [])[:10],
                    "experience_years": c.get("experience_years"),
                    "location": c.get("location"),
                    "similarity_score": c.get("similarity_score"),
                    "summary": c.get("summary", "")[:200]
                }
                for c in candidates[:10]
            ],
            "total_count": len(candidates)
        }
        
        rag_logger.info("Response generated successfully")
        
        # Update messages with assistant response
        messages_update = [AIMessage(content=response_text)]
        
        return {
            "response_text": response_text,
            "structured_response": structured_response,
            "messages": messages_update
        }
        
    except Exception as e:
        rag_logger.error(f"Error generating response: {str(e)}")
        error_message = "I encountered an error generating the response. Please try again."
        return {
            "response_text": error_message,
            "structured_response": {
                "type": "error",
                "message": error_message
            },
            "error": str(e)
        }
