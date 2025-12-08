from fastapi import APIRouter

from .gender import router as gender_router
from .interests import router as interests_router
from .orientation import router as orientation_router
from .options import router as profile_options_router
from .profile import router as profile_router
from .photos import router as photos_router

router = APIRouter(prefix="/profile", tags=["Profile"])

# router.include_router(gender_router)
# router.include_router(interests_router)
# router.include_router(orientation_router)
router.include_router(profile_options_router)
router.include_router(photos_router)
router.include_router(profile_router)

__all__=["router"]