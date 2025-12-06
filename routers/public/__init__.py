from .auth import router as auth_router
from .profile import router as profile_router
from .user import router as user_router

__all__ = ['auth_router', 'profile_router', 'user_router']