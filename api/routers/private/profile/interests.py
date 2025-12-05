from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.db import get_db
from middleware.auth import auth_user
from schemas.preferences import InterestsEnum

from typing import List
from controllers.interests import _get_all_interest_options, _get_profile_interests, _delete_profile_interests, _interest_name_to_id, _interests_to_id_arr, _update_profile_interests

router = APIRouter(prefix="/me/interests", tags=["Profile: Interests"])

# API ENDPOINTS
@router.get("")
def get_my_profile_interests(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_profile_interests(uid=uid, db=db)

"""Take in an array of user interests, and update the profiles.interests to add those. 
We delete previous interests because the payload will be the list of new interests, not just additional ones
"""
@router.post("")
def update_profile_interests(payload: List[InterestsEnum], uid: str = Depends(auth_user), db: Session = Depends(get_db), ):
     return _update_profile_interests(payload=payload, uid=uid, db=db)

"""Delete all existing interests for a given user"""
@router.delete("")
def delete_profile_interests(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _delete_profile_interests(uid=uid, db=db)