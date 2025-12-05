from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.db import get_db
from services.otp import send_otp, verify_otp
from fastapi.encoders import jsonable_encoder
from schemas.auth.phone import PhoneOTPAnswerSchema

from typing import Annotated
from controllers.auth import _register_user_phone, _check_phone_claimed_by

router = APIRouter(prefix="/phone", tags=["Authentication: Phone OTP"])

"""This sends a "short-code" (6 digits) to the desired phone number. Phone must be in 10 digit format (prefix +1)"""
@router.get("/otp")
def send_phone_otp(phone: str):
    res = send_otp(phone=phone) # handles validity already
    return res

"""This will return a JWT access token that the frontend will use to provide the backend for CRUD operations that need user authorization"""
@router.post("/otp")
def verify_phone_otp(payload: PhoneOTPAnswerSchema, db: Annotated[Session, Depends(get_db)]):
    payload = jsonable_encoder(payload)
    res = verify_otp(phone=payload.get("phone"), code=payload.get("code")) # handles validity already
    user_data = jsonable_encoder(res).get("user")
    _register_user_phone(user_data=user_data, db=db) # register potentially new user to users db table if not already
    return res
