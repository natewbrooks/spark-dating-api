from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException

from schemas.preferences import UserProfilePreferencesSchema
from controllers.user import _user_exists
from controllers.gender import _gender_name_to_id

from json import dumps

def _user_prefs_exist(uid: str, db: Session):
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' does not exist!")

    stmt = text("""SELECT 1 FROM users.preferences WHERE uid = :uid LIMIT 1""")
    return bool(db.execute(stmt, {"uid": uid}).scalar())

def _get_user_prefs(uid: str, db: Session):
    stmt = text("""SELECT * FROM users.preferences WHERE uid = :uid LIMIT 1""")
    prefs = db.execute(stmt, {"uid": uid}).mappings().one()
    if not prefs:
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' has no preferences!")
        
    return prefs 


def _create_user_prefs(payload: UserProfilePreferencesSchema, uid: str, db: Session):
    if _user_prefs_exist(uid=uid, db=db):
        raise HTTPException(status_code=409, detail=f"User with id '{uid}' already has preferences! Use 'PUT' to update them!")
    
    payload = jsonable_encoder(payload)
    target_gender_name = payload.get("target_gender")
    tgid = _gender_name_to_id(target_gender_name, db=db)

    stmt = text("""
        INSERT INTO users.preferences (uid, target_gender_id, age_min, age_max, max_distance, extra_options)
            VALUES (:uid, :tgid, :age_min, :age_max, :max_distance, :extra_options)
    """)

    db.execute(stmt, {"uid": uid, "tgid": tgid, "age_min": payload.get("age_min"), "age_max": payload.get("age_max"), "max_distance": payload.get("max_distance"), "extra_options": dumps(payload.get("extra_options"))})
    return {"ok": True}

def _update_user_prefs(payload: UserProfilePreferencesSchema, uid: str, db: Session):
    if not _user_prefs_exist(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"The user with id '{uid}' does not have preferences created yet!")

    payload = jsonable_encoder(payload)
    target_gender_name = payload.get("target_gender")
    tgid = _gender_name_to_id(target_gender_name, db=db)

    stmt = text("""
        UPDATE users.preferences
        SET 
            target_gender_id = :tgid,
            age_min = :age_min,
            age_max = :age_max,
            max_distance = :max_distance,
            extra_options = :extra_options,
            updated_at = now()
        WHERE uid = :uid
    """)

    db.execute(stmt, {"uid": uid, "tgid": tgid, "age_min": payload.get("age_min"), "age_max": payload.get("age_max"), "max_distance": payload.get("max_distance"), "extra_options": dumps(payload.get("extra_options"))})
    return {"ok": True}