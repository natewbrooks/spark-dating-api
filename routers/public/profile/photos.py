from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from middleware.auth import auth_user
from models.db import get_db

from schemas.photos import PhotoMetaSchema
from typing import Annotated, List

import asyncio
from controllers.profile import _profile_exists
from services.supabase import supabase_for_service
from services.storage import get_user_photos

router = APIRouter(tags=["Profile: Photos"])

@router.get("/{target_uid}/photos", response_model=List[PhotoMetaSchema])
async def get_user_profile_photos(
    target_uid: str,
    caller_uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)]
):
    if not _profile_exists(target_uid, db=db):
        raise HTTPException(status_code=404, detail="Profile not found")
    # TODO: enforce blocks/visibility before fetching

    storage = supabase_for_service.storage
    result = await asyncio.to_thread(
        get_user_photos,
        storage=storage,
        uid=target_uid,
        db=db,
        ttl_seconds=500,
        only_approved=True, 
    )
    return result
