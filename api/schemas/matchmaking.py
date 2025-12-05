from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field
from schemas.preferences import UserProfilePreferencesSchema

class MatchmakingQueueSchema(BaseModel):
    uid: UUID
    mode_id: UUID
    enqueued_at: str
    prefs_snapshot: UserProfilePreferencesSchema
    location_snapshot: str
    expires_at: str