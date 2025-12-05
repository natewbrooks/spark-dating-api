from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from controllers.profile import _profile_exists

def _orientation_name_to_id(name: str, db: Session):
    id = db.execute(text("SELECT id FROM public.orientations WHERE name = :name LIMIT 1"), {"name": name}).scalar()
    if id:
        return id
    else:
        raise HTTPException(status_code=400, detail=f"Orientation '{name}' is not registered in the database!")

def _orientation_id_to_name(id: str, db: Session):
    name = db.execute(text("SELECT name FROM public.orientations WHERE id = :id LIMIT 1"), {"id": id}).scalar()
    if name:
        return name
    else:
        raise HTTPException(status_code=400, detail=f"Orientation with id '{id}' is not registered in the database!")

def _get_all_orientation_options(db: Session):
    res = db.execute(text("SELECT * FROM public.orientations")).mappings().all()
    return res

def _get_profile_orientation(uid: str, db: Session):
    if not _profile_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"Profile with uid '{uid}' does not exist!")
   
    orientation_id = db.execute(text("SELECT orientation_id FROM profiles.profiles WHERE uid = :uid LIMIT 1"), {"uid": uid}).scalar()
    return {
        "name": _orientation_id_to_name(id=orientation_id, db=db),
        "id": orientation_id
    }

def _update_profile_orientation(orientation_id: str, uid: str, db: Session):
    if not _profile_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"Profile with uid '{uid}' does not exist!")
    
    stmt = text("""
        UPDATE profiles.profiles
        SET orientation_id = :orientation_id
        WHERE uid = :uid
    """)

    db.execute(stmt, {"orientation_id": orientation_id, "uid": uid})
    return {"ok": True}
