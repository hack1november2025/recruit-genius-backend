"""Repository for chat message operations."""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import BaseRepository
from app.db.models.chat_message import ChatMessage


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for chat message operations."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ChatMessage, db)
    
    async def get_by_session(self, session_id: int, limit: int | None = None) -> list[ChatMessage]:
        """
        Get all messages for a chat session, ordered by creation time.
        
        Args:
            session_id: ID of the chat session
            limit: Optional limit on number of messages to return
            
        Returns:
            List of messages ordered by created_at
        """
        query = (
            select(self.model)
            .where(self.model.session_id == session_id)
            .order_by(self.model.created_at.asc())
        )
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_recent_messages(self, session_id: int, limit: int = 10) -> list[ChatMessage]:
        """
        Get recent messages for a chat session.
        
        Args:
            session_id: ID of the chat session
            limit: Maximum number of recent messages to return
            
        Returns:
            List of recent messages ordered by created_at descending
        """
        result = await self.db.execute(
            select(self.model)
            .where(self.model.session_id == session_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        # Reverse to get chronological order
        return list(reversed(messages))
    
    async def create_message(
        self,
        session_id: int,
        role: str,
        content: str,
        candidate_ids: List[int] | None = None,
        message_metadata: dict | None = None
    ) -> ChatMessage:
        """
        Create a new chat message.
        
        Args:
            session_id: ID of the chat session
            role: Message role ('user' or 'assistant')
            content: Message content
            candidate_ids: List of candidate IDs referenced in the message
            message_metadata: Additional metadata
            
        Returns:
            Created ChatMessage
        """
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            candidate_ids=candidate_ids or [],
            message_metadata=message_metadata or {}
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def delete_session_messages(self, session_id: int) -> int:
        """
        Delete all messages for a session.
        
        Args:
            session_id: ID of the chat session
            
        Returns:
            Number of messages deleted
        """
        messages = await self.get_by_session(session_id)
        count = len(messages)
        
        for message in messages:
            await self.db.delete(message)
        
        await self.db.commit()
        return count
