from fastapi import APIRouter

from .user import router as user_router
from .chats import router as chats_router
from .preferences import router as preferences_router

router = APIRouter(prefix="/user", tags=["User"])

router.include_router(user_router)
router.include_router(chats_router)
router.include_router(preferences_router)

__all__=["router"]