from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel

class UserInfoSchema(BaseModel):
    fname: str
    lname: str
    birthdate: datetime
    