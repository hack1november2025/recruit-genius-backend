"""Service for conversational AI-powered job description generation."""
from app.agents.job_generator.graph import create_job_generator_graph
from langchain_core.messages import HumanMessage
from app.core.logging import llm_logger


class JobGeneratorService:
    """Service for conversational job description generation."""
    
    def __init__(self):
        self.graph = None
    
    async def initialize(self):
        """Initialize the agent graph with async checkpointer."""
        if not self.graph:
            self.graph = await create_job_generator_graph()
            llm_logger.info("Job generator graph initialized")
    
    async def chat(self, message: str, thread_id: str) -> str:
        """
        Chat with the job generator agent.
        
        Args:
            message: User message (e.g., "Create job for senior Python developer")
            thread_id: Conversation thread ID for persistence
        
        Returns:
            Agent's markdown response
        """
        await self.initialize()
        
        # Prepare configuration with thread_id for checkpointing
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Prepare initial state
        initial_state = {
            "messages": [HumanMessage(content=message)]
        }
        
        # Invoke graph
        result = await self.graph.ainvoke(initial_state, config=config)
        
        # Extract last AI message
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            llm_logger.info(f"Generated response for thread {thread_id}")
            return response
        
        return "No response generated."
    
    async def stream_chat(self, message: str, thread_id: str):
        """
        Stream chat responses from the agent.
        
        Args:
            message: User message
            thread_id: Conversation thread ID
        
        Yields:
            Markdown chunks as they're generated
        """
        await self.initialize()
        
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        initial_state = {
            "messages": [HumanMessage(content=message)]
        }
        
        # Stream graph execution
        async for event in self.graph.astream(initial_state, config=config):
            # Extract AI messages from events
            for node_name, node_output in event.items():
                if "messages" in node_output:
                    messages = node_output["messages"]
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.content:
                            yield msg.content

