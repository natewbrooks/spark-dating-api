from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel

class UserInfoSchema(BaseModel):
    first_name: str
    last_name: str
    birthdate: datetime
    