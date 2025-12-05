from __future__ import annotations

from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field
from schemas.preferences.interests import InterestsEnum

class SessionModeSchema(BaseModel):
    name: str
    time_limit: int
    interest: Optional[InterestsEnum]
    config: Optional[object]