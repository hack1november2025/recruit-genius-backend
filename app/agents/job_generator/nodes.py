"""Node functions for job generator agent."""
from langchain_core.messages import AIMessage, SystemMessage, trim_messages
from langchain_openai import ChatOpenAI
from app.agents.job_generator.state import JobGeneratorState
from app.agents.job_generator.tools import save_job_to_database
from app.core.config import get_settings
from app.core.logging import llm_logger


settings = get_settings()

# Create LLM with tool binding
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0.7, 
    openai_api_key=settings.openai_api_key
)
llm_with_tools = llm.bind_tools([save_job_to_database])


# System prompt for the job generator agent
SYSTEM_PROMPT = """You are an expert HR job description writer. Your role is to:

1. **Generate job descriptions** from brief user input
2. **Refine and modify** descriptions based on user feedback
3. **Save to database** when user approves (using save_job_to_database tool)

## Guidelines:
- Always respond ONLY in **markdown format**
- Keep the full job description in your context so you can modify it
- Listen carefully to user requests: "make it more friendly", "add remote work", etc.
- When generating, include:
  - Job title as H1 (# Title)
  - Key sections: About, Responsibilities, Requirements, Benefits
  - Use bullet points for lists
  - Professional but engaging tone
- Check for inclusive language (avoid "rockstar", "ninja", age references)
- ONLY use the save_job_to_database tool when user explicitly approves:
  - "looks good", "save it", "create the job", "that's perfect", etc.
  
## Workflow:
1. User provides brief → Generate full markdown job description
2. User requests changes → Modify the description accordingly  
3. User approves → Call save_job_to_database tool with extracted title/description
4. After saving → Confirm and offer to create another

Remember: Maintain context! Keep refining the SAME job description unless user starts a completely new request.
Remember: Maintain context! Keep refining the SAME job description unless user starts a completely new request."""


def trim_messages_middleware(state: JobGeneratorState) -> dict:
    """Trim messages to keep conversation within context window."""
    messages = state["messages"]
    
    # Keep system message + last 10 messages
    if len(messages) <= 11:
        return {}
    
    # Trim but keep system message
    from langchain_core.messages import trim_messages
    
    trimmed = trim_messages(
        messages,
        max_tokens=4000,
        strategy="last",
        token_counter=len,  # Simple token counter
        include_system=True,
    )
    
    llm_logger.debug(f"Trimmed messages from {len(messages)} to {len(trimmed)}")
    return {"messages": trimmed}


async def call_model(state: JobGeneratorState) -> dict:
    """
    Main agent node that processes user message and generates/modifies job descriptions.
    """
    messages = state["messages"]
    
    # Prepend system message if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # Call LLM with tools
    response = await llm_with_tools.ainvoke(messages)
    
    llm_logger.info("Agent responded")
    
    return {"messages": [response]}


async def call_tools(state: JobGeneratorState) -> dict:
    """Execute tool calls from the agent."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # Get tool calls from last message
    tool_calls = getattr(last_message, "tool_calls", [])
    
    if not tool_calls:
        return {}
    
    # Execute tools using ToolNode (LangGraph 0.2.x pattern)
    from langgraph.prebuilt import ToolNode
    tool_node = ToolNode([save_job_to_database])
    
    llm_logger.info(f"Executing {len(tool_calls)} tool(s)")
    
    # ToolNode handles the execution and message formatting
    result = await tool_node.ainvoke(state)
    
    return result


def route_after_agent(state: JobGeneratorState) -> str:
    """Route to tools if there are tool calls, otherwise end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_calls = getattr(last_message, "tool_calls", [])
    
    if tool_calls:
        return "tools"
    return "end"
