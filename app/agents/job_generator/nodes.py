"""Node functions for job generator agent."""
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, trim_messages, RemoveMessage
from langchain_openai import ChatOpenAI
from app.agents.job_generator.state import JobGeneratorState
from app.agents.job_generator.tools import save_job_to_database
from app.core.config import get_settings
from app.core.logging import llm_logger
from app.core.langfuse_config import get_langfuse_callbacks


settings = get_settings()

# Create LLM with tool binding
llm = ChatOpenAI(
    model=settings.llm_model, 
    temperature=0.7, 
    openai_api_key=settings.openai_api_key
)
llm_with_tools = llm.bind_tools([save_job_to_database])

# Summarization LLM (same model, but for summarization)
summarization_llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0,  # Lower temperature for consistent summaries
    openai_api_key=settings.openai_api_key
)


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


async def summarize_messages(state: JobGeneratorState) -> dict:
    """
    Summarization middleware: When conversation gets too long, summarize old messages.
    
    This prevents context window overflow by:
    1. Keeping recent messages intact (last 6 messages)
    2. Summarizing older messages into a single summary
    3. Always preserving the system message
    
    Triggered when message count exceeds threshold.
    """
    messages = state["messages"]
    
    # Threshold: summarize if we have more than 12 messages
    # (system + 1 summary + 10 recent messages)
    if len(messages) <= 12:
        return {}
    
    llm_logger.info(f"Summarizing conversation: {len(messages)} messages")
    
    # Separate system message, old messages, and recent messages
    system_msg = messages[0] if isinstance(messages[0], SystemMessage) else None
    start_idx = 1 if system_msg else 0
    
    # Keep last 6 messages (3 exchanges), summarize the rest
    messages_to_summarize = messages[start_idx:-6]
    recent_messages = messages[-6:]
    
    if not messages_to_summarize:
        return {}
    
    # Create summary prompt
    summary_prompt = f"""Condense this job description conversation into a brief summary.
Focus on:
- What job was being created/modified
- Key requirements and changes requested
- Current state of the job description

Conversation to summarize:
{chr(10).join([f"{m.type}: {m.content[:200]}..." if len(m.content) > 200 else f"{m.type}: {m.content}" for m in messages_to_summarize])}

Provide a concise summary (2-3 sentences):"""
    
    # Get summary from LLM
    callbacks = get_langfuse_callbacks(
        session_id=state.get("session_id"),
        trace_name="job_generator_summarization",
        tags=["job_generator", "summarization"],
        metadata={"message_count": len(messages_to_summarize)}
    )
    summary_response = await summarization_llm.ainvoke(
        [HumanMessage(content=summary_prompt)],
        config={"callbacks": callbacks}
    )
    summary_text = summary_response.content
    
    llm_logger.info(f"Created summary: {summary_text[:100]}...")
    
    # Build new message list:
    # 1. System message (if exists)
    # 2. Summary message
    # 3. Recent messages
    new_messages = []
    if system_msg:
        new_messages.append(system_msg)
    
    # Add summary as a human message labeled as summary
    new_messages.append(
        HumanMessage(
            content=f"[Previous conversation summary]: {summary_text}"
        )
    )
    
    # Add recent messages
    new_messages.extend(recent_messages)
    
    llm_logger.info(f"Reduced messages from {len(messages)} to {len(new_messages)}")
    
    return {"messages": new_messages}


async def call_model(state: JobGeneratorState) -> dict:
    """
    Main agent node that processes user message and generates/modifies job descriptions.
    """
    messages = state["messages"]
    
    # Prepend system message if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    # Get Langfuse callbacks with session context
    callbacks = get_langfuse_callbacks(
        session_id=state.get("session_id"),
        trace_name="job_generator_agent",
        tags=["job_generator", "agent", "generation"],
        metadata={"message_count": len(messages)}
    )
    
    # Call LLM with tools and Langfuse tracking
    response = await llm_with_tools.ainvoke(messages, config={"callbacks": callbacks})
    
    llm_logger.info("Agent responded")
    
    return {"messages": [response]}


async def call_tools(state: JobGeneratorState) -> dict:
    """
    Execute tool calls from the agent.
    
    Custom implementation to properly handle async database operations
    instead of using LangChain's ToolNode which has issues with SQLAlchemy async.
    """
    from langchain_core.messages import ToolMessage
    
    messages = state["messages"]
    last_message = messages[-1]
    
    # Get tool calls from last message
    tool_calls = getattr(last_message, "tool_calls", [])
    
    if not tool_calls:
        return {}
    
    llm_logger.info(f"Executing {len(tool_calls)} tool(s)")
    
    tool_messages = []
    
    # Execute each tool call
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        
        llm_logger.info(f"Calling tool: {tool_name} with args: {tool_args}")
        
        try:
            # Execute the tool - it handles its own async context internally
            if tool_name == "save_job_to_database":
                result = await save_job_to_database.coroutine(**tool_args)
            else:
                result = f"Unknown tool: {tool_name}"
            
            llm_logger.info(f"Tool {tool_name} executed successfully")
            
            # Create tool message with result
            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
            
        except Exception as e:
            llm_logger.error(f"Tool execution failed: {str(e)}", exc_info=True)
            
            # Create error message
            tool_message = ToolMessage(
                content=f"Error executing {tool_name}: {str(e)}",
                tool_call_id=tool_call_id,
                name=tool_name
            )
            tool_messages.append(tool_message)
    
    return {"messages": tool_messages}


def route_after_agent(state: JobGeneratorState) -> str:
    """Route to tools if there are tool calls, otherwise end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    tool_calls = getattr(last_message, "tool_calls", [])
    
    if tool_calls:
        return "tools"
    return "end"
