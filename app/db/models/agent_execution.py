from sqlalchemy import Column, Integer, String, Text, JSON, Enum as SQLEnum
from app.db.base import Base, TimestampMixin
import enum


class AgentType(str, enum.Enum):
    """Agent type enum."""
    RESUME_ANALYZER = "resume_analyzer"
    JOB_MATCHER = "job_matcher"
    INTERVIEWER = "interviewer"


class ExecutionStatus(str, enum.Enum):
    """Execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentExecution(Base, TimestampMixin):
    """Agent execution tracking model."""
    
    __tablename__ = "agent_executions"
    
    agent_type = Column(SQLEnum(AgentType), nullable=False, index=True)
    thread_id = Column(String(255), nullable=False, index=True)
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    status = Column(
        SQLEnum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
        nullable=False,
        index=True
    )
    error_message = Column(Text, nullable=True)
    execution_metadata = Column(JSON, nullable=True)
