from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import get_db
from middleware.auth import auth_user
from sqlalchemy import text
from typing import Annotated
from controllers.user import _get_user_by_id

router = APIRouter()

@router.get("/{target_uid}")
def get_user_info(
    target_uid: str,
    caller_uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)]
):
    return _get_user_by_id(uid=target_uid, db=db)