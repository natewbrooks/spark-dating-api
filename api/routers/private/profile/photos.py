import asyncio
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from middleware.auth import auth_user, get_user_jwt
from models.db import get_db
from services.storage import upload_profile_photo, get_user_photos, delete_profile_photo, update_profile_photo, update_profile_photo_metadata

from services.supabase import storage_for_user

from schemas.photos import PhotoMetaSchema, PhotoSchema, UpdatePhotoMetaSchema
from typing import Annotated, List


router = APIRouter(prefix="/me/photos", tags=["Profile: Photos"])

@router.get("", response_model=List[PhotoMetaSchema])
async def get_profile_photos(uid: Annotated[str, Depends(auth_user)], user_jwt: Annotated[str, Depends(get_user_jwt)], db: Annotated[Session, Depends(get_db)]):
    storage = storage_for_user(user_jwt=user_jwt)
    result = await asyncio.to_thread(
        get_user_photos,
        uid=uid,
        db=db,
        storage=storage,
        ttl_seconds=500
    )

    return result

@router.post("")
async def add_profile_photo(photo: UploadFile, user_jwt: Annotated[str, Depends(get_user_jwt)], uid: Annotated[str, Depends(auth_user)], db: Annotated[Session, Depends(get_db)]):
    photo_bytes = await photo.read()
    if not photo_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    storage = storage_for_user(user_jwt=user_jwt)

    result = await asyncio.to_thread(
        upload_profile_photo,
        uid=uid,
        file_bytes=photo_bytes,
        mime_type=photo.content_type,
        db=db,
        storage=storage
    )

    return {
        "message": "Photo uploaded successfully",
        "photo": result,
    }

import json

@router.put("")
async def set_profile_photo(
    photo: Annotated[str, Form()],
    new_photo: UploadFile,
    user_jwt: Annotated[str, Depends(get_user_jwt)],
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)]
):
    # Convert JSON string to dict, then to PhotoSchema
    try:
        photo_dict = json.loads(photo)  # String → Dict
        photo_schema = PhotoSchema(**photo_dict)  # Dict → Pydantic model
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid photo data: {str(e)}")
    
    new_photo_bytes = await new_photo.read()
    if not new_photo_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")
    
    storage = storage_for_user(user_jwt=user_jwt)
    result = await asyncio.to_thread(
        update_profile_photo,
        photo=photo_schema,
        uid=uid,
        file_bytes=new_photo_bytes,
        mime_type=new_photo.content_type,
        db=db,
        storage=storage
    )
    
    return {
        "message": "Photo updated successfully",
        "photo": result,
    }

@router.put("/meta")
async def set_profile_photo_metadata(
    data: UpdatePhotoMetaSchema,
    user_jwt: Annotated[str, Depends(get_user_jwt)],
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)]
):
    storage = storage_for_user(user_jwt=user_jwt)
    
    result = await asyncio.to_thread(
        update_profile_photo_metadata,
        photo=data.photo,
        metadata=data.metadata,
        uid=uid,
        db=db,
        storage=storage
    )
    
    return {
        "message": "Photo metadata updated successfully",
        "photo": result,
    }

@router.delete("")
async def del_profile_photo(photo: PhotoSchema, user_jwt: Annotated[str, Depends(get_user_jwt)], uid: Annotated[str, Depends(auth_user)], db: Annotated[Session, Depends(get_db)]):
    storage = storage_for_user(user_jwt=user_jwt)
    result = await asyncio.to_thread(
        delete_profile_photo,
        photo=photo,
        uid=uid,
        db=db,
        storage=storage
    )

    return {
        "message": "Photo deleted successfully",
        "photo": result,
    }
