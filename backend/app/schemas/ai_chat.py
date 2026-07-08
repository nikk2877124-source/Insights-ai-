from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    dataset_id: int
    question: str


class ChatResponse(BaseModel):
    answer: str


class ChatHistoryItem(BaseModel):
    id: int
    dataset_id: int
    user_id: int
    question: str
    answer: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    history: list[ChatHistoryItem]

