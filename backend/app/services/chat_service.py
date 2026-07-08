from __future__ import annotations

from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.models.user import User
from app.services.ai_services import AIService
from app.services.dataset_services import get_latest_dataset_profile, get_user_dataset


class ChatService:
    """Service responsible for chat conversations persistence and retrieval."""

    def __init__(self):
        self.ai_service = AIService()

    def save_conversation(
        self,
        db: Session,
        *,
        dataset_id: int,
        user_id: int,
        question: str,
        answer: str,
    ) -> ChatHistory:
        chat = ChatHistory(
            dataset_id=dataset_id,
            user_id=user_id,
            question=question,
            answer=answer,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    def retrieve_history(
        self,
        db: Session,
        *,
        dataset_id: int,
        user_id: int,
        limit: int | None = 100,
    ) -> List[ChatHistory]:
        q = db.query(ChatHistory).filter(
            ChatHistory.dataset_id == dataset_id,
            ChatHistory.user_id == user_id,
        )
        q = q.order_by(ChatHistory.created_at.desc())
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def chat(
        self,
        db: Session,
        *,
        dataset_id: int,
        user: User,
        question: str,
    ) -> ChatHistory:
        # Ownership verification (requirement #5)
        dataset = get_user_dataset(db, dataset_id, user.id)

        latest_profile = get_latest_dataset_profile(db, dataset.id)
        profile_json = latest_profile.profile_json or {}
        if not isinstance(profile_json, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid dataset profile payload",
            )

        answer = self.ai_service.chat_with_dataset(
            question=question,
            dataset_profile=profile_json,
        )

        # Store every conversation (requirement #6)
        return self.save_conversation(
            db,
            dataset_id=dataset.id,
            user_id=user.id,
            question=question,
            answer=answer,
        )

