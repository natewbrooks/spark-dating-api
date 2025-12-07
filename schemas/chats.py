from uuid import UUID
from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel
from .user import UserInfoSchema

class ChatMessageSchema(BaseModel):
    id: UUID
    created_at: datetime
    author_uid: UUID
    receiver_uid: Optional[UUID]
    content: str
    is_system: bool
    source: Literal["session", "direct"]

class ChatListItemSchema(BaseModel):
    id: UUID
    match_session_id: UUID
    last_message_at: datetime
    status: str
    other_user: UserInfoSchema
    last_message: Optional[ChatMessageSchema]

class ChatDetailSchema(BaseModel):
    id: UUID
    match_session_id: UUID
    last_message_at: datetime
    status: str
    other_user: UserInfoSchema
    messages: List[ChatMessageSchema]
