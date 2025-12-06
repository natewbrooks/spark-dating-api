from .profile import router as profile_router
from .user import router as user_router
from .matchmaking import router as matchmaking_router

__all__ = ['profile_router', 'user_router', 'matchmaking_router']