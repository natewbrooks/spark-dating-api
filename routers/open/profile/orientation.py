from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import get_db
from middleware.auth import auth_user
from typing import Annotated
from controllers.profile import _profile_exists

from schemas.preferences.sexual_orientation import SexualOrientationsEnum 
from controllers.orientation import _get_profile_orientation, _get_all_orientation_options, _orientation_name_to_id, _update_profile_orientation

router = APIRouter(tags=["Profile: Orientation"])

@router.get("/orientations")
def get_all_orientation_options(db: Session = Depends(get_db)):
    return _get_all_orientation_options(db=db)

@router.get("/{target_uid}/orientation")
def get_user_profile_orientation(
    target_uid: str,
    caller_uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)]
):
   return _get_profile_orientation(uid=target_uid, db=db)