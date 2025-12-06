from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import get_db
from middleware.auth import auth_user

from typing import Annotated
from controllers.profile import _get_profile

router = APIRouter()

@router.get("/{target_uid}")
def get_user_profile(
    target_uid: str,
    caller_uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)]
):
    return _get_profile(uid=target_uid, db=db)