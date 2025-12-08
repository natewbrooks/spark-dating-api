from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from typing import Dict, Any, List, Union
from schemas.preferences import UserProfilePreferencesSchema
from controllers.user import _user_exists
from controllers.profile_options import _name_to_id, _id_to_name
from json import dumps


def _to_list(value):
    """Convert value to list if it isn't already."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _user_prefs_exist(uid: str, db: Session):
    """Check if user has preferences row created."""
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(
            status_code=404, 
            detail=f"User with id '{uid}' does not exist!"
        )
    
    stmt = text("""SELECT 1 FROM users.preferences WHERE uid = :uid LIMIT 1""")
    return bool(db.execute(stmt, {"uid": uid}).scalar())


def _get_user_prefs(uid: str, db: Session) -> Dict[str, Any]:
    """
    Retrieves a user's matchmaking preferences from users.preferences table.
    Returns core preferences + extra options from the JSONB column.
    """
    
    # Get preferences from users.preferences (including JSONB extra_options)
    stmt = text("""
        SELECT age_min, age_max, max_distance, target_gender_id, extra_options
        FROM users.preferences 
        WHERE uid = :uid 
        LIMIT 1
    """)
    prefs_result = db.execute(stmt, {"uid": uid}).mappings().one_or_none()
    
    if not prefs_result:
        raise HTTPException(
            status_code=404, 
            detail=f"User with id '{uid}' has no preferences!"
        )
    
    prefs = dict(prefs_result)
    
    # Convert target_gender_id to name
    target_gender_id = prefs.get("target_gender_id")
    if target_gender_id:
        try:
            prefs["target_gender"] = _id_to_name(target_gender_id, "genders", db)
        except HTTPException:
            prefs["target_gender"] = None
    
    # extra_options is already in JSONB format, just return it
    # (it will be None or a dict)
    
    return prefs


def _create_user_prefs(payload: UserProfilePreferencesSchema, uid: str, db: Session):
    """Create user preferences (core + extra options)."""
    
    if _user_prefs_exist(uid=uid, db=db):
        raise HTTPException(
            status_code=409, 
            detail=f"User with id '{uid}' already has preferences! Use 'PUT' to update them!"
        )
    
    payload_dict = jsonable_encoder(payload)
    
    # Get target gender ID
    target_gender_name = payload_dict.get("target_gender")
    target_gender_id = _name_to_id(target_gender_name, "genders", db)
    
    # Get extra options (will be stored as JSONB)
    extra_options = payload_dict.get("extra_options")
    
    # Create preferences row
    stmt = text("""
        INSERT INTO users.preferences (uid, target_gender_id, age_min, age_max, max_distance, extra_options)
        VALUES (:uid, :tgid, :age_min, :age_max, :max_distance, :extra_options)
    """)
    db.execute(stmt, {
        "uid": uid,
        "tgid": target_gender_id,
        "age_min": payload_dict.get("age_min"),
        "age_max": payload_dict.get("age_max"),
        "max_distance": payload_dict.get("max_distance"),
        "extra_options": dumps(extra_options) if extra_options else None
    })
    
    return {"ok": True}


def _update_user_prefs(payload: UserProfilePreferencesSchema, uid: str, db: Session):
    """Update user preferences (core + extra options)."""
    if not _user_prefs_exist(uid=uid, db=db):
        return _create_user_prefs(payload=payload, uid=uid, db=db)

    payload_dict = jsonable_encoder(payload)

    target_gender_name = payload_dict.get("target_gender")
    target_gender_id = _name_to_id(target_gender_name, "genders", db)

    extra_options = payload_dict.get("extra_options")

    print(f"\n{'='*80}")
    print(f"DEBUG: Updating preferences for uid={uid}")
    print(f"DEBUG: target_gender={target_gender_name} → {target_gender_id}")
    print(f"DEBUG: age_min={payload_dict.get('age_min')}")
    print(f"DEBUG: age_max={payload_dict.get('age_max')}")
    print(f"DEBUG: max_distance={payload_dict.get('max_distance')}")
    print(f"DEBUG: extra_options={extra_options}")
    print(f"{'='*80}\n")

    stmt = text("""
        UPDATE users.preferences
        SET 
            target_gender_id = :tgid,
            age_min          = :age_min,
            age_max          = :age_max,
            max_distance     = :max_distance,
            extra_options    = :extra_options,
            updated_at       = NOW()
        WHERE uid = :uid
    """)

    try:
        result = db.execute(
            stmt,
            {
                "uid": uid,
                "tgid": target_gender_id,
                "age_min": payload_dict.get("age_min"),
                "age_max": payload_dict.get("age_max"),
                "max_distance": payload_dict.get("max_distance"),
                "extra_options": dumps(extra_options) if extra_options is not None else None,
            },
        )
        
        print(f"DEBUG: UPDATE executed, rowcount={result.rowcount}")
        
        if result.rowcount == 0:
            print(f"WARNING: No rows updated for uid={uid}")
        else:
            print(f"Preferences updated successfully!")
            
    except Exception as e:
        print(f"ERROR updating preferences: {e}")
        raise

    return {"ok": True}