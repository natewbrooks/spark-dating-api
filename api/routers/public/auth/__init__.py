from fastapi import APIRouter

from .auth import router as auth_router
from .phone import router as phone_router

router = APIRouter(prefix="/auth", tags=["Authentication"])

router.include_router(phone_router)
router.include_router(auth_router)

__all__=["router"]