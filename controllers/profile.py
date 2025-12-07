from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException

from controllers.user import _user_exists

def _profile_exists(uid: str, db: Session) -> bool:
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' does not exist!")
    
    return bool(
        db.execute(
            text("""SELECT 1 FROM profiles.profiles WHERE uid = :uid LIMIT 1"""),
            {"uid": uid}
        ).scalar()
    )

def _get_profile(uid: str, db: Session):
    stmt = text("""
        SELECT 
            p.*,
            u.birthdate
        FROM profiles.profiles p
        JOIN users.users u
          ON u.id = p.uid
        WHERE p.uid = :uid
        LIMIT 1
    """)
    profile = db.execute(stmt, {'uid': uid}).mappings().first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile