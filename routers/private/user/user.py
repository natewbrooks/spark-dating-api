from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import get_db
from middleware.auth import auth_user
from schemas.user import UserInfoSchema

from controllers.user import _user_exists, _toggle_user_pause, _update_user_info, _get_user_by_id, _soft_delete_user

router = APIRouter(prefix="/me")


@router.get("")
def get_my_user_info(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_user_by_id(uid=uid, db=db)
    
@router.put("/pause")
def toggle_pause_user(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _toggle_user_pause(uid=uid, db=db)

"""Used the first time after a user registers, to set/update their non-changeable info (e.g. birthdate, first name, last name, etc.)"""
@router.put("")
def set_user_info(payload: UserInfoSchema, uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _update_user_info(payload=payload, uid=uid, db=db)

@router.delete("")
def temp_delete_user(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _soft_delete_user(uid=uid, db=db)