from sqlalchemy import text
from sqlalchemy.orm import Session
from controllers.user import _user_exists

from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException

from controllers.user import _create_user

def _check_phone_claimed_by(phone: str, db: Session):
    stmt = text("SELECT id from users.users WHERE phone = :phone LIMIT 1")
    claimed_by = db.execute(stmt, {"phone": phone}).scalar()
    # Convert UUID to string for comparison
    if claimed_by is not None:
        claimed_by = str(claimed_by)
    return claimed_by

"""This is used to add a newly authenticated user to the users db table if they aren't already added"""
def _register_user_phone(user_data: object, db: Session):
    data = jsonable_encoder(user_data)
    uid = data.get("id")
    exists = _user_exists(uid=uid, db=db)
    provider = (data.get("app_metadata") or {}).get("provider")
    
    if provider != "phone":
        return {"ok": True}
    
    phone = data.get("phone")
    if not phone:
        return {"ok": True}
    
    phone_claimed_by = _check_phone_claimed_by(phone=phone, db=db)
    
    # If phone is claimed by another user, raise error
    if phone_claimed_by is not None and phone_claimed_by != uid:
        raise HTTPException(
            status_code=409,
            detail=f"Phone number {phone} is already registered to another account",
        )
    
    # If phone is claimed by current user and user exists, return ok
    if phone_claimed_by == uid and exists:
        return {"ok": True}
    
    # If user doesn't exist and phone is unclaimed, create user
    if not exists and phone_claimed_by is None:
        return _create_user(uid=uid, phone=phone, db=db)
    
    return {"ok": True}