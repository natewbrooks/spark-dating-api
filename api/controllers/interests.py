from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from schemas.preferences import InterestsEnum
from controllers.profile import _profile_exists
from controllers.user import _user_exists

from typing import List


def _interest_name_to_id(name: str, db: Session) -> str | HTTPException:
    id = db.execute(text("SELECT id FROM public.interests WHERE name = :name LIMIT 1"), {"name": name}).scalar()
    if id:
        return id
    else:
        raise HTTPException(status_code=400, detail=f"User interest '{name}' is not registered in the database!")

def _interest_id_to_name(id: str, db: Session) -> str | HTTPException:
    name = db.execute(text("SELECT name FROM public.interests WHERE id = :id LIMIT 1"), {"id": id}).scalar()
    if name:
        return name
    else:
        raise HTTPException(status_code=400, detail=f"User interest with id '{id}' is not registered in the database!")

def _interests_to_id_arr(arr: List[str], db: Session) -> List[str]:
    res: list[str] = []
    for interest in arr:
        id = _interest_name_to_id(name=interest, db=db)
        res.append(id)
    return res

def _get_all_interest_options(db: Session):
    res = db.execute(text("SELECT * FROM public.interests")).mappings().all()
    return res

def _get_profile_interests(uid: str, db: Session):
    if not _profile_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"Profile with id '{uid}' does not exist!")

    rows = db.execute(text("SELECT interest_id FROM profiles.interests WHERE uid = :uid"), {"uid": uid}).mappings().all()

    return [
        {
            "name": _interest_id_to_name(row["interest_id"], db),
            "id": row["interest_id"]
        } for row in rows
    ]

def _update_profile_interests(payload: List[InterestsEnum], uid: str, db: Session):
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' does not exist!")
    
    payload = jsonable_encoder(payload)
    interest_ids = _interests_to_id_arr(payload, db=db) # List of str
    _delete_profile_interests(uid=uid, db=db) # Delete existing user interests for said user

    for interest_id in interest_ids:
        stmt = text("""
            INSERT INTO profiles.interests (uid, interest_id)
            VALUES (:uid, :interest_id)
        """)
        db.execute(stmt, {"uid": uid, "interest_id": interest_id})
    return {"ok": True}

"""Delete all existing interests for a given user"""
def _delete_profile_interests(uid: str, db: Session):
    stmt = text("""
        DELETE FROM profiles.interests
        WHERE uid = :uid
    """)
    db.execute(stmt, {"uid": uid})
    return {"ok": True}