from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from models.db import get_db
from middleware.auth import auth_user

from schemas.profile import UserProfileSchema

from controllers.profile import _get_profile, _create_profile, _update_profile

router = APIRouter(prefix='/me')

@router.get("")
def get_my_profile(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Retrieves the authenticated user's complete dating profile.
    """
    profile = _get_profile(uid=uid, db=db)
    if not profile:
         raise HTTPException(status_code=404, detail=f"Profile for user '{uid}' not found.")
    return profile

@router.post("")
def create_profile(payload: UserProfileSchema, uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Used the first time after a user registers, to create their dating profile.
    """
    payload_dict = jsonable_encoder(payload)
    return _create_profile(uid=uid, payload=payload_dict, db=db)


@router.put("")
def update_profile(payload: UserProfileSchema, uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    """
    Used to update a user's profile information. Creates the profile if it doesn't exist.
    """
    payload_dict = jsonable_encoder(payload)
    return _update_profile(uid=uid, payload=payload_dict, db=db)