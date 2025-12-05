from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from schemas.user import UserInfoSchema

def _user_exists(uid: str, db: Session) -> bool:
    return bool(
        db.execute(
            text("SELECT 1 FROM users.users WHERE id = :id LIMIT 1"),
            {"id": uid}
        ).scalar()
    )
    
def _create_user(uid: str, phone: str, db: Session):
    stmt = text("""
        INSERT INTO users.users (id, phone, created_at)
        VALUES (:id, :phone, now())
    """)
    
    user = db.execute(stmt, {"id": uid, "phone": phone})
    return user

def _get_user_by_id(uid: str, db: Session):
    """Private helper to fetch user by ID"""
    stmt = text("""
        SELECT * FROM users.users WHERE id = :uid LIMIT 1
    """)
    return db.execute(stmt, {"uid": uid}).mappings().first()

def _set_user_online(uid: str, db: Session):
    """Sets the user's online status to True and updates last seen timestamp."""
    if not _user_exists(uid=uid, db=db):
        # User not found; typically acceptable during socket connect if user is new,
        # but we need to ensure the user is created elsewhere if they don't exist.
        return None 
    
    stmt = text("""
        UPDATE users.users 
        SET is_online = TRUE, last_seen_at = now()
        WHERE id = :uid
        RETURNING id
    """)
    res = db.execute(stmt, {"uid": uid}).mappings().first()
    return res

def _set_user_offline(uid: str, db: Session):
    """Sets the user's online status to False and updates last seen timestamp."""
    if not _user_exists(uid=uid, db=db):
        return None 

    stmt = text("""
        UPDATE users.users 
        SET is_online = FALSE, last_seen_at = now()
        WHERE id = :uid
        RETURNING id
    """)
    res = db.execute(stmt, {"uid": uid}).mappings().first()
    return res

def _toggle_user_pause(uid: str, db: Session):
    """Private helper to toggle user's paused status"""
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail="User not found")

    stmt = text("""
        UPDATE users.users 
        SET paused = NOT paused
        WHERE id = :uid
        RETURNING *
    """)
    return db.execute(stmt, {"uid": uid}).mappings().first()


def _update_user_info(payload: UserInfoSchema, uid: str, db: Session):
    """Private helper to update user's non-changeable info (first use only)"""
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail="User not found")
    
    payload = jsonable_encoder(payload)
    stmt = text("""
        UPDATE users.users AS u
        SET
        first_name = COALESCE(NULLIF(u.first_name, ''), :fn),
        last_name  = COALESCE(NULLIF(u.last_name,  ''), :ln),
        birthdate  = COALESCE(u.birthdate, :dob)
        WHERE u.id = :uid
        AND (
            u.first_name IS NULL OR u.first_name = '' OR
            u.last_name  IS NULL OR u.last_name  = '' OR
            u.birthdate  IS NULL
        )
        RETURNING first_name, last_name, birthdate
    """)
    
    db.execute(stmt, {"fn": payload.get("fname"), "ln": payload.get("lname"), "dob": payload.get("dob"), "uid": uid})
    return _get_user_by_id(uid, db)

def _soft_delete_user(uid: str, db: Session):
    """Private helper to soft delete user by setting deleted_at timestamp"""
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail="User not found")

    stmt = text("""
        UPDATE users.users 
        SET deleted_at = now()
        WHERE id = :uid
        RETURNING *
    """)
    return db.execute(stmt, {"uid": uid}).mappings().first()