from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.db import get_db
from middleware.auth import auth_user

from schemas.preferences import GendersEnum
from controllers.gender import _gender_name_to_id, _get_all_gender_options, _get_profile_gender, _update_profile_gender

from sqlalchemy import text
from typing import Annotated
from controllers.profile import _profile_exists

router = APIRouter(tags=["Profile: Gender"])

@router.get("/genders")
def get_all_gender_options(db: Session = Depends(get_db)):
    return _get_all_gender_options(db=db)

@router.get("/{target_uid}/gender")
def get_user_profile_gender(
    target_uid: str,
    caller_uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)]
):
    return _get_profile_gender(uid=target_uid, db=db)