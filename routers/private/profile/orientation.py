from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import get_db
from middleware.auth import auth_user

from schemas.preferences.orientation import UpdateSexualOrientationSchema
from controllers.orientation import _get_profile_orientation, _get_all_orientation_options, _orientation_name_to_id, _update_profile_orientation

router = APIRouter(prefix="/me/orientation", tags=["Profile: Orientation"])

@router.get("")
def get_profile_orientation(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_profile_orientation(uid=uid, db=db)
    
@router.put("")
def update_profile_orientation(payload: UpdateSexualOrientationSchema, uid = Depends(auth_user), db: Session = Depends(get_db)):
    payload = jsonable_encoder(payload)
    gid = _orientation_name_to_id(name=payload.get("orientation"), db=db)
    return _update_profile_orientation(orientation_id=gid, uid=uid, db=db)