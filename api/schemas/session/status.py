from enum import Enum

class SessionStatusEnum(Enum):
    open = "open"
    closed = "closed"
    matched = "matched"
    abandoned = "abandoned"