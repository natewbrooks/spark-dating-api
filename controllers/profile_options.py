from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException
from typing import List, Any, Optional, Union

# --- Utility Functions (unchanged) ---

def _profile_exists(uid: str, db: Session) -> bool:
    count = db.execute(text("SELECT count(*) FROM profiles.profiles WHERE uid = :uid"), {"uid": uid}).scalar()
    return count > 0

def _user_exists(uid: str, db: Session) -> bool:
    return db.execute(text("SELECT count(*) FROM users.users WHERE id = :uid"), {"uid": uid}).scalar() > 0


# --- Generic helper functions (like interests/genders/orientations pattern) ---

def _name_to_id(name: Union[str, List[str]], table_name: str, db: Session) -> Union[str, List[str]]:
    """Convert an option name(s) to its ID(s) from a lookup table.
    Handles both single strings and lists of strings.
    """
    
    # 1. Handle list of names (Multi-Select)
    if isinstance(name, list):
        if not name:
            return []  # Return empty list if input is empty
        
        # CRITICAL FIX: Create individual placeholders for each name
        # SQLAlchemy's text() cannot bind Python lists directly to IN clauses
        placeholders = ', '.join([f':name_{i}' for i in range(len(name))])
        query = text(f"SELECT id FROM public.{table_name} WHERE name IN ({placeholders})")
        
        # Create parameter dict with individual parameters
        params = {f'name_{i}': val for i, val in enumerate(name)}
        
        result = db.execute(query, params).scalars().all()
        
        # Check if all names were found - warn but don't fail
        if len(result) != len(name):
            found_count = len(result)
            expected_count = len(name)
            missing = set(name) - set([params[f'name_{i}'] for i in range(len(name)) if f'name_{i}' in params])
            print(f"Warning: Only found {found_count} out of {expected_count} options in table '{table_name}'")
            print(f"Missing values: {missing}")
        
        return list(result)
    
    # 2. Handle single name (Single-Select - original logic)
    else:
        id_result = db.execute(
            text(f"SELECT id FROM public.{table_name} WHERE name = :name LIMIT 1"), 
            {"name": name}
        ).scalar()
        
        if id_result:
            return id_result
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Option '{name}' not found in table '{table_name}'!"
            )


def _id_to_name(id: str, table_name: str, db: Session) -> str:
    """Convert an ID to its name from a lookup table."""
    name = db.execute(
        text(f"SELECT name FROM public.{table_name} WHERE id = :id LIMIT 1"), 
        {"id": id}
    ).scalar()
    
    if name:
        return name
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"ID '{id}' not found in table '{table_name}'!"
        )


def _list_to_id_arr(arr: List[str], table_name: str, db: Session) -> List[str]:
    """
    Convert a list of option names to a list of IDs.
    """
    return _name_to_id(arr, table_name, db)


# ----------------------------------------------------------------------
# DISPATCHER MAPPING
# ----------------------------------------------------------------------

# Format: "endpoint_key": (lookup_table, db_column_or_table, storage_type)
# Storage types:
#   'SINGLE_FK' - Single foreign key in profiles.profiles
#   'JUNCTION'  - Many-to-many via junction table in profiles schema
#   'PREF_FK'   - Foreign key in users.preferences (target_gender)

TABLE_MAPPING = {
    # Match Preference (in users.preferences)
    "target_gender": ("genders", "target_gender_id", 'PREF_FK'),
    
    # Single-Value Profile Fields (FK in profiles.profiles)
    "relationship_goals": ("relationship_goals", "relationship_goal_id", 'SINGLE_FK'),
    "personality_types": ("personality_types", "personality_type_id", 'SINGLE_FK'),
    "love_languages": ("love_languages", "love_language_id", 'SINGLE_FK'),
    "attachment_styles": ("attachment_styles", "attachment_style_id", 'SINGLE_FK'),
    "political_views": ("political_views", "political_view_id", 'SINGLE_FK'),
    "zodiac_signs": ("zodiac_signs", "zodiac_sign_id", 'SINGLE_FK'),
    "religions": ("religions", "religion_id", 'SINGLE_FK'),
    "diets": ("diets", "diet_id", 'SINGLE_FK'),
    "exercise_frequencies": ("exercise_frequencies", "exercise_frequency_id", 'SINGLE_FK'),
    "smoke_frequencies": ("smoke_frequencies", "smoke_frequency_id", 'SINGLE_FK'),
    "drink_frequencies": ("drink_frequencies", "drink_frequency_id", 'SINGLE_FK'),
    "sleep_schedules": ("sleep_schedules", "sleep_schedule_id", 'SINGLE_FK'),
    "pronouns": ("pronouns", "pronoun_id", 'SINGLE_FK'),
    
    # Multi-Value Profile Fields (Junction tables)
    "languages_spoken": ("languages", "languages_spoken", 'JUNCTION'),
    "interests": ("interests", "interests", 'JUNCTION'),
    "pets": ("pets", "pets", 'JUNCTION'),
    "sexual_orientations": ("orientations", "sexual_orientations", 'JUNCTION'),
}


# ----------------------------------------------------------------------
# GET IMPLEMENTATIONS
# ----------------------------------------------------------------------

def _get_single_value(uid: str, db: Session, lookup_table: str, column_name: str, storage_type: str) -> Optional[dict]:
    """Get a single FK value from profiles.profiles or users.preferences."""
    
    if storage_type == 'SINGLE_FK':
        if not _profile_exists(uid, db):
            raise HTTPException(status_code=404, detail=f"Profile with id '{uid}' not found.")
        
        # Get FK ID from profiles.profiles
        stmt = text(f"SELECT {column_name} FROM profiles.profiles WHERE uid = :uid")
        option_id = db.execute(stmt, {"uid": uid}).scalar_one_or_none()
        
        if option_id is None:
            return None
        
        # Get name from lookup table
        name = _id_to_name(option_id, lookup_table, db)
        return {"name": name, "id": option_id}
    
    elif storage_type == 'PREF_FK':
        # Get FK ID from users.preferences (target_gender_id)
        stmt = text(f"SELECT {column_name} FROM users.preferences WHERE uid = :uid")
        option_id = db.execute(stmt, {"uid": uid}).scalar_one_or_none()
        
        if option_id is None:
            return None
        
        name = _id_to_name(option_id, lookup_table, db)
        return {"name": name, "id": option_id}
    
    return None


def _get_multi_value(uid: str, db: Session, lookup_table: str, junction_table: str) -> List[dict]:
    """Get multiple values from a junction table (e.g., profiles.interests)."""
    
    if not _profile_exists(uid, db):
        raise HTTPException(status_code=404, detail=f"Profile with id '{uid}' not found.")
    
    # Query junction table for IDs
    stmt = text(f"SELECT {lookup_table[:-1]}_id FROM profiles.{junction_table} WHERE uid = :uid")
    rows = db.execute(stmt, {"uid": uid}).mappings().all()
    
    if not rows:
        return []
    
    # Get names for each ID
    result = []
    for row in rows:
        option_id = row[f"{lookup_table[:-1]}_id"]
        name = _id_to_name(option_id, lookup_table, db)
        result.append({"name": name, "id": option_id})
    
    return result


# ----------------------------------------------------------------------
# UPDATE IMPLEMENTATIONS
# ----------------------------------------------------------------------

def _update_single_value(uid: str, db: Session, lookup_table: str, column_name: str, storage_type: str, payload: Any) -> dict:
    """Update a single FK value in profiles.profiles or users.preferences."""
    
    if not _user_exists(uid, db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' not found.")
    
    option_name = str(payload)
    option_id = _name_to_id(option_name, lookup_table, db)
    
    if storage_type == 'SINGLE_FK':
        # Update FK in profiles.profiles
        stmt = text(f"""
            UPDATE profiles.profiles 
            SET {column_name} = :option_id, updated_at = NOW() 
            WHERE uid = :uid
        """)
        db.execute(stmt, {"option_id": option_id, "uid": uid})
        db.commit()
        return {"ok": True, column_name.replace('_id', ''): option_name}
    
    elif storage_type == 'PREF_FK':
        # Update FK in users.preferences
        # Ensure preferences row exists
        _ensure_preferences_row(uid, db)
        
        stmt = text(f"""
            UPDATE users.preferences 
            SET {column_name} = :option_id, updated_at = NOW() 
            WHERE uid = :uid
        """)
        db.execute(stmt, {"option_id": option_id, "uid": uid})
        db.commit()
        return {"ok": True, column_name.replace('_id', ''): option_name}
    
    raise HTTPException(status_code=500, detail="Update logic missing for storage type.")


def _update_multi_value(uid: str, db: Session, lookup_table: str, junction_table: str, payload: List[Any]) -> dict:
    """Update multiple values in a junction table (e.g., profiles.interests)."""
    
    if not _user_exists(uid, db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' not found.")
    
    # Convert enum names to IDs
    option_names = [str(item) for item in payload]
    option_ids = _list_to_id_arr(option_names, lookup_table, db)
    
    # Delete existing entries
    _delete_multi_value(uid, db, junction_table)
    
    # Insert new entries
    column_name = f"{lookup_table[:-1]}_id"  # e.g., "interest_id" from "interests"
    
    for option_id in option_ids:
        stmt = text(f"""
            INSERT INTO profiles.{junction_table} (uid, {column_name})
            VALUES (:uid, :option_id)
        """)
        db.execute(stmt, {"uid": uid, "option_id": option_id})
    
    db.commit()
    return {"ok": True, "count": len(option_ids)}


# ----------------------------------------------------------------------
# DELETE IMPLEMENTATIONS
# ----------------------------------------------------------------------

def _delete_single_value(uid: str, db: Session, column_name: str, storage_type: str) -> dict:
    """Delete/clear a single FK value."""
    
    if not _user_exists(uid, db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' not found.")
    
    if storage_type == 'SINGLE_FK':
        # Set FK to NULL in profiles.profiles
        stmt = text(f"""
            UPDATE profiles.profiles 
            SET {column_name} = NULL, updated_at = NOW() 
            WHERE uid = :uid
        """)
        db.execute(stmt, {"uid": uid})
        db.commit()
        return {"ok": True, "message": f"Cleared {column_name.replace('_id', '')}."}
    
    elif storage_type == 'PREF_FK':
        # Reset target_gender_id to 'any'
        default_gender_id = db.execute(
            text("SELECT id FROM genders WHERE name = 'any'")
        ).scalar_one_or_none()
        
        if not default_gender_id:
            raise HTTPException(status_code=500, detail="Default target gender 'any' not found.")
        
        stmt = text("""
            UPDATE users.preferences 
            SET target_gender_id = :default_id, updated_at = NOW() 
            WHERE uid = :uid
        """)
        db.execute(stmt, {"default_id": default_gender_id, "uid": uid})
        db.commit()
        return {"ok": True, "message": "Reset target_gender to 'any'."}
    
    raise HTTPException(status_code=500, detail="Delete logic missing for storage type.")


def _delete_multi_value(uid: str, db: Session, junction_table: str) -> dict:
    """Delete all entries from a junction table for a user."""
    
    if not _user_exists(uid, db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' not found.")
    
    stmt = text(f"""
        DELETE FROM profiles.{junction_table}
        WHERE uid = :uid
    """)
    db.execute(stmt, {"uid": uid})
    db.commit()
    
    return {"ok": True, "message": f"Cleared all {junction_table}."}


# ----------------------------------------------------------------------
# HELPER: Ensure preferences row exists
# ----------------------------------------------------------------------

def _ensure_preferences_row(uid: str, db: Session):
    """Ensures the users.preferences row exists (for target_gender updates)."""
    default_gender_id = db.execute(
        text("SELECT id FROM genders WHERE name = 'any'")
    ).scalar_one_or_none()
    
    if not default_gender_id:
        raise HTTPException(status_code=500, detail="Default target gender 'any' not found.")

    stmt = text("""
        INSERT INTO users.preferences (uid, age_min, age_max, max_distance, target_gender_id)
        VALUES (:uid, 18, 70, 50, :default_gender_id)
        ON CONFLICT (uid) DO NOTHING;
    """)
    db.execute(stmt, {"uid": uid, "default_gender_id": default_gender_id})
    db.commit()


# ----------------------------------------------------------------------
# DISPATCHER FUNCTION
# ----------------------------------------------------------------------

def dispatch_preference_action(
    action: str, 
    key: str, 
    uid: str, 
    db: Session, 
    payload: Optional[Any] = None
) -> Any:
    """
    Main dispatcher for all preference actions.
    
    Args:
        action: 'get', 'update', or 'delete'
        key: The preference key (e.g., 'interests', 'relationship_goals')
        uid: User ID
        db: Database session
        payload: Data for update actions
    
    Returns:
        Result of the action (dict or list)
    """
    
    if key not in TABLE_MAPPING:
        raise HTTPException(status_code=404, detail=f"Preference type '{key}' not supported.")
    
    lookup_table, target_key, storage_type = TABLE_MAPPING[key]
    
    # Handle multi-value (junction table) preferences
    if storage_type == 'JUNCTION':
        if action == "get":
            return _get_multi_value(uid, db, lookup_table, target_key)
        elif action == "update":
            if not isinstance(payload, List):
                payload = jsonable_encoder(payload)
                if not isinstance(payload, List):
                    raise HTTPException(
                        status_code=422, 
                        detail="Update payload must be a list for multi-value options."
                    )
            return _update_multi_value(uid, db, lookup_table, target_key, payload)
        elif action == "delete":
            return _delete_multi_value(uid, db, target_key)
    
    # Handle single-value (FK) preferences
    elif storage_type in ['SINGLE_FK', 'PREF_FK']:
        if action == "get":
            return _get_single_value(uid, db, lookup_table, target_key, storage_type)
        elif action == "update":
            return _update_single_value(uid, db, lookup_table, target_key, storage_type, payload)
        elif action == "delete":
            return _delete_single_value(uid, db, target_key, storage_type)
    
    raise HTTPException(status_code=500, detail="Controller action failed.")