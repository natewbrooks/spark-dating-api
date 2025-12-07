from enum import Enum

class SessionStatusEnum(Enum):
    open = "open"
    closed = "closed"
    found = "found"
    abandoned = "abandoned"