from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from middleware.auth import auth_user
from models.db import get_db

from controllers.preferences import _update_user_prefs, _create_user_prefs, _get_user_prefs
from schemas.preferences import UserProfilePreferencesSchema

router = APIRouter(prefix="/me/preferences", tags=["User: Preferences"])

# API ENDPOINTS
@router.get("")
def get_my_user_prefs(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_user_prefs(uid=uid, db=db)

@router.put("")
def update_user_prefs(payload: UserProfilePreferencesSchema, uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _update_user_prefs(payload=payload, uid=uid, db=db)

@router.post("")
def create_user_prefs(payload: UserProfilePreferencesSchema, uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _create_user_prefs(payload=payload, uid=uid, db=db)
