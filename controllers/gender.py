from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from controllers.profile import _profile_exists

def _gender_name_to_id(name: str, db: Session):
    id = db.execute(text("SELECT id FROM public.genders WHERE name = :name LIMIT 1"), {"name": name}).scalar()
    if id:
        return id
    else:
        raise HTTPException(status_code=400, detail=f"Gender '{name}' is not registered in the database!")
    
def _gender_id_to_name(id: str, db: Session):
    name = db.execute(text("SELECT name FROM public.genders WHERE id = :id LIMIT 1"), {"id": id}).scalar()
    if name:
        return name
    else:
        raise HTTPException(status_code=400, detail=f"Gender id '{id}' is not registered in the database!")
    

def _get_all_gender_options(db: Session):
    res = db.execute(text("SELECT * FROM public.genders")).mappings().all()
    return res

def _get_profile_gender(uid: str, db: Session):
    if not _profile_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"Profile with id '{uid}' does not exist!")
    
    gender_id = db.execute(text("SELECT gender_id FROM profiles.profiles WHERE uid = :uid LIMIT 1"), {"uid": uid}).scalar()
    return {
        "name": _gender_id_to_name(id=gender_id, db=db),
        "id": gender_id
    }


def _update_profile_gender(gender_id: str, uid: str, db: Session):
    if not _profile_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"Profile with id '{uid}' does not exist!")

    stmt = text("""
        UPDATE profiles.profiles
        SET gender_id = :gender_id
        WHERE uid = :uid
    """)

    db.execute(stmt, {"gender_id": gender_id, "uid": uid})
    return {"ok": True}