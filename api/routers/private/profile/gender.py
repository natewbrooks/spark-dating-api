from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from models.db import get_db
from middleware.auth import auth_user

from schemas.preferences import UpdateGenderSchema
from controllers.gender import _gender_name_to_id, _get_all_gender_options, _get_profile_gender, _update_profile_gender

router = APIRouter(prefix="/me/gender", tags=["Profile: Gender"])

@router.get("")
def get_profile_gender(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_profile_gender(uid=uid, db=db)

@router.put("")
def update_profile_gender(payload: UpdateGenderSchema, uid = Depends(auth_user), db: Session = Depends(get_db)):
    payload = jsonable_encoder(payload)
    gid = _gender_name_to_id(name=payload.get("gender"), db=db)
    return _update_profile_gender(gender_id=gid, uid=uid, db=db)