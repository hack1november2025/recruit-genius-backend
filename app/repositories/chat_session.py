"""Repository for chat session operations."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models.chat_session import ChatSession


class ChatSessionRepository(BaseRepository[ChatSession]):
    """Repository for chat session operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ChatSession, db)
    
    async def get_with_messages(self, session_id: int) -> ChatSession | None:
        """
        Get chat session with all its messages loaded.
        
        Args:
            session_id: ID of the chat session
            
        Returns:
            ChatSession with messages relationship loaded, or None
        """
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(self.model)
            .options(selectinload(self.model.messages))
            .where(self.model.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_recent_sessions(self, limit: int = 20) -> list[ChatSession]:
        """
        Get most recent chat sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of recent chat sessions
        """
        result = await self.db.execute(
            select(self.model)
            .order_by(self.model.updated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_session_timestamp(self, session_id: int) -> ChatSession | None:
        """
        Update the session's updated_at timestamp.
        
        Args:
            session_id: ID of the chat session
            
        Returns:
            Updated ChatSession or None
        """
        session = await self.get(session_id)
        if session:
            # SQLAlchemy will automatically update the updated_at timestamp
            await self.db.commit()
            await self.db.refresh(session)
        return session
