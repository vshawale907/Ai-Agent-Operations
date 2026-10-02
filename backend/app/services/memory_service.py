"""
Conversation Memory Service.

Manages multi-turn conversation threads and persists user/assistant message history.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models.conversation import ChatMessageModel, Conversation

logger = get_logger(__name__)


class MemoryService:
    """Manages multi-turn conversation threads and persists context."""

    async def get_or_create_conversation(
        self,
        db: AsyncSession,
        user_id: int,
        conversation_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Conversation:
        """Get an existing conversation thread or create a new one."""
        if conversation_id:
            stmt = (
                select(Conversation)
                .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
                .options(selectinload(Conversation.messages))
            )
            res = await db.execute(stmt)
            conv = res.scalars().first()
            if conv:
                return conv

        # Create new
        new_conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title or "New Analysis Session",
        )
        db.add(new_conv)
        await db.commit()
        await db.refresh(new_conv)
        return new_conv

    async def get_recent_history(
        self,
        db: AsyncSession,
        conversation_id: str,
        limit: int = 6,
    ) -> List[Dict[str, str]]:
        """Retrieve recent conversation history as [{"role": "user"|"assistant", "content": "..."}]."""
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.conversation_id == conversation_id)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        messages = list(res.scalars().all())
        messages.reverse()

        return [{"role": m.role, "content": m.content} for m in messages]

    async def save_turn(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_content: str,
        assistant_content: str,
        intent: Optional[str] = None,
        chart_data: Optional[Dict[str, Any]] = None,
        table_data: Optional[List[Dict[str, Any]]] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record both user message and assistant response in conversation thread."""
        user_msg = ChatMessageModel(
            conversation_id=conversation_id,
            role="user",
            content=user_content,
        )
        assistant_msg = ChatMessageModel(
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_content,
            intent=intent,
            chart_data=chart_data,
            table_data=table_data,
            citations=citations,
            metadata_json=metadata_json,
        )
        db.add(user_msg)
        db.add(assistant_msg)
        await db.commit()
        logger.info(f"Saved chat turn to conversation_id={conversation_id}")


memory_service = MemoryService()
