from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field
from .status import SessionStatusEnum

class SessionSchema(BaseModel):
    host_uid: UUID
    guest_uid: UUID
    status: SessionStatusEnum
    prompt: str
    started_at: str
    closed_at: Optional[str] = None
    mode_id: UUID

class CreateSessionSchema(BaseModel):
    # host_uid: UUID
    mode_id: UUID