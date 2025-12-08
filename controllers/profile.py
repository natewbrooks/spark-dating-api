from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, List, Optional
from controllers.user import _user_exists
from schemas.profile import UserProfileSchema

def _profile_exists(uid: str, db: Session) -> bool:
    if not _user_exists(uid=uid, db=db):
        raise HTTPException(status_code=404, detail=f"User with id '{uid}' does not exist!")
    
    return bool(
        db.execute(
            text("""SELECT 1 FROM profiles.profiles WHERE uid = :uid LIMIT 1"""),
            {"uid": uid}
        ).scalar()
    )


def _name_to_id(name: str, table_name: str, db: Session) -> str:
    """Convert an option name to its ID from a lookup table."""
    if not name:
        return None
        
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


def _id_to_name(id: str, table_name: str, db: Session) -> Optional[str]:
    """Convert an ID to its name from a lookup table."""
    if not id:
        return None
        
    name = db.execute(
        text(f"SELECT name FROM public.{table_name} WHERE id = :id LIMIT 1"), 
        {"id": id}
    ).scalar()
    
    return name


def _names_to_ids(names: List[str], table_name: str, db: Session) -> List[str]:
    """Convert a list of names to IDs."""
    if not names:
        return []
    
    placeholders = ', '.join([f':name_{i}' for i in range(len(names))])
    query = text(f"SELECT id FROM public.{table_name} WHERE name IN ({placeholders})")
    params = {f'name_{i}': val for i, val in enumerate(names)}
    
    return list(db.execute(query, params).scalars().all())


def _update_junction_table(uid: str, table_name: str, fk_column: str, values: List[str], lookup_table: str, db: Session):
    """Update a junction table (delete old, insert new)."""
    # Delete existing
    db.execute(
        text(f"DELETE FROM profiles.{table_name} WHERE uid = :uid"),
        {"uid": uid}
    )
    
    if not values:
        return
    
    # Convert names to IDs
    ids = _names_to_ids(values, lookup_table, db)
    
    # Insert new
    for id_val in ids:
        db.execute(
            text(f"INSERT INTO profiles.{table_name} (uid, {fk_column}) VALUES (:uid, :id)"),
            {"uid": uid, "id": id_val}
        )


def _get_junction_values(uid: str, table_name: str, fk_column: str, lookup_table: str, db: Session) -> List[str]:
    """Get values from a junction table."""
    rows = db.execute(
        text(f"SELECT {fk_column} FROM profiles.{table_name} WHERE uid = :uid"),
        {"uid": uid}
    ).fetchall()
    
    if not rows:
        return []
    
    # Convert IDs to names
    names = []
    for row in rows:
        name = _id_to_name(row[0], lookup_table, db)
        if name:
            names.append(name)
    
    return names


def _get_profile(uid: str, db: Session) -> Dict[str, Any]:
    """
    Retrieves a user's profile and converts all foreign key IDs to human-readable strings.
    Also loads junction table data (interests, pets, languages_spoken).
    """
    
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
    profile_result = db.execute(stmt, {'uid': uid}).mappings().one_or_none()
    
    if not profile_result:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Convert the result into a mutable dictionary
    profile = dict(profile_result)

    # Convert all FK IDs to names
    fk_mappings = {
        "gender_id": "genders",
        "orientation_id": "orientations",
        "pronoun_id": "pronouns",
        "relationship_goal_id": "relationship_goals",
        "personality_type_id": "personality_types",
        "love_language_id": "love_languages",
        "attachment_style_id": "attachment_styles",
        "political_view_id": "political_views",
        "zodiac_sign_id": "zodiac_signs",
        "religion_id": "religions",
        "diet_id": "diets",
        "exercise_frequency_id": "exercise_frequencies",
        "smoke_frequency_id": "smoke_frequencies",
        "drink_frequency_id": "drink_frequencies",
        "sleep_schedule_id": "sleep_schedules",
    }
    
    for fk_field, lookup_table in fk_mappings.items():
        fk_id = profile.get(fk_field)
        field_name = fk_field.replace('_id', '')
        if fk_id:
            profile[field_name] = _id_to_name(fk_id, lookup_table, db)
        else:
            profile[field_name] = None
    
    # Load junction table data
    profile["interests"] = _get_junction_values(uid, "interests", "interest_id", "interests", db)
    profile["pets"] = _get_junction_values(uid, "pets", "pet_id", "pets", db)
    profile["languages_spoken"] = _get_junction_values(uid, "languages_spoken", "language_id", "languages", db)
    
    return profile


def _create_profile(uid: str, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Inserts a new profile record for the user.
    Converts all enum names to FK IDs.
    """
    if _profile_exists(uid=uid, db=db): 
        raise HTTPException(status_code=409, detail=f"Profile for user with uid '{uid}' is already created! Use 'PUT' to update it.")

    try:
        # Convert names to IDs for FK fields
        gender_id = _name_to_id(payload.get("gender"), "genders", db) if payload.get("gender") else None
        orientation_id = _name_to_id(payload.get("orientation"), "orientations", db) if payload.get("orientation") else None
        pronoun_id = _name_to_id(payload.get("pronouns"), "pronouns", db) if payload.get("pronouns") else None
        relationship_goal_id = _name_to_id(payload.get("relationship_goal"), "relationship_goals", db) if payload.get("relationship_goal") else None
        personality_type_id = _name_to_id(payload.get("personality_type"), "personality_types", db) if payload.get("personality_type") else None
        love_language_id = _name_to_id(payload.get("love_language"), "love_languages", db) if payload.get("love_language") else None
        attachment_style_id = _name_to_id(payload.get("attachment_style"), "attachment_styles", db) if payload.get("attachment_style") else None
        political_view_id = _name_to_id(payload.get("political_view"), "political_views", db) if payload.get("political_view") else None
        zodiac_sign_id = _name_to_id(payload.get("zodiac_sign"), "zodiac_signs", db) if payload.get("zodiac_sign") else None
        religion_id = _name_to_id(payload.get("religion"), "religions", db) if payload.get("religion") else None
        diet_id = _name_to_id(payload.get("diet"), "diets", db) if payload.get("diet") else None
        exercise_frequency_id = _name_to_id(payload.get("exercise_frequency"), "exercise_frequencies", db) if payload.get("exercise_frequency") else None
        smoke_frequency_id = _name_to_id(payload.get("smoke_frequency"), "smoke_frequencies", db) if payload.get("smoke_frequency") else None
        drink_frequency_id = _name_to_id(payload.get("drink_frequency"), "drink_frequencies", db) if payload.get("drink_frequency") else None
        sleep_schedule_id = _name_to_id(payload.get("sleep_schedule"), "sleep_schedules", db) if payload.get("sleep_schedule") else None
        
        # drug_use and weed_use: Store enum names directly (not FKs)
        drug_use = payload.get("drug_use")
        weed_use = payload.get("weed_use")

        stmt = text("""
        INSERT INTO profiles.profiles (
            uid, bio, drug_use, weed_use, gender_id, orientation_id, 
            location, location_label, show_precise_location, pronoun_id, 
            school, occupation, relationship_goal_id, 
            personality_type_id, love_language_id, attachment_style_id, political_view_id, 
            zodiac_sign_id, religion_id, diet_id, exercise_frequency_id, 
            smoke_frequency_id, drink_frequency_id, sleep_schedule_id
        )
        VALUES (
            :uid, :bio, :drug_use, :weed_use, :gender_id, :orientation_id,
            :location, :location_label, :show_precise_location, :pronoun_id,
            :school, :occupation, :relationship_goal_id,
            :personality_type_id, :love_language_id, :attachment_style_id, :political_view_id,
            :zodiac_sign_id, :religion_id, :diet_id, :exercise_frequency_id,
            :smoke_frequency_id, :drink_frequency_id, :sleep_schedule_id
        ) RETURNING uid
        """)

        params = {
            "uid": uid,
            "bio": payload.get("bio"),
            "drug_use": drug_use,
            "weed_use": weed_use,
            "gender_id": gender_id,
            "orientation_id": orientation_id,
            "location": payload.get("location"),
            "location_label": payload.get("location_label"),
            "show_precise_location": payload.get("show_precise_location"),
            "pronoun_id": pronoun_id,
            "school": payload.get("school"),
            "occupation": payload.get("occupation"),
            "relationship_goal_id": relationship_goal_id,
            "personality_type_id": personality_type_id,
            "love_language_id": love_language_id,
            "attachment_style_id": attachment_style_id,
            "political_view_id": political_view_id,
            "zodiac_sign_id": zodiac_sign_id,
            "religion_id": religion_id,
            "diet_id": diet_id,
            "exercise_frequency_id": exercise_frequency_id,
            "smoke_frequency_id": smoke_frequency_id,
            "drink_frequency_id": drink_frequency_id,
            "sleep_schedule_id": sleep_schedule_id,
        }
        
        db.execute(stmt, params)
        
        # Handle junction tables
        if payload.get("interests"):
            _update_junction_table(uid, "interests", "interest_id", payload["interests"], "interests", db)
        if payload.get("pets"):
            _update_junction_table(uid, "pets", "pet_id", payload["pets"], "pets", db)
        if payload.get("languages_spoken"):
            _update_junction_table(uid, "languages_spoken", "language_id", payload["languages_spoken"], "languages", db)
        
        return {"ok": True, "detail": f"Profile for user '{uid}' created."}
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during profile creation: {e}")


def _update_profile(uid: str, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Updates an existing profile record for the user.
    Converts all enum names to FK IDs.
    """
    if not _profile_exists(uid=uid, db=db):
        # Fallback to creation if profile doesn't exist
        return _create_profile(uid=uid, payload=payload, db=db)
    
    try:
        # Convert names to IDs for FK fields
        gender_id = _name_to_id(payload.get("gender"), "genders", db) if payload.get("gender") else None
        orientation_id = _name_to_id(payload.get("orientation"), "orientations", db) if payload.get("orientation") else None
        pronoun_id = _name_to_id(payload.get("pronouns"), "pronouns", db) if payload.get("pronouns") else None
        relationship_goal_id = _name_to_id(payload.get("relationship_goal"), "relationship_goals", db) if payload.get("relationship_goal") else None
        personality_type_id = _name_to_id(payload.get("personality_type"), "personality_types", db) if payload.get("personality_type") else None
        love_language_id = _name_to_id(payload.get("love_language"), "love_languages", db) if payload.get("love_language") else None
        attachment_style_id = _name_to_id(payload.get("attachment_style"), "attachment_styles", db) if payload.get("attachment_style") else None
        political_view_id = _name_to_id(payload.get("political_view"), "political_views", db) if payload.get("political_view") else None
        zodiac_sign_id = _name_to_id(payload.get("zodiac_sign"), "zodiac_signs", db) if payload.get("zodiac_sign") else None
        religion_id = _name_to_id(payload.get("religion"), "religions", db) if payload.get("religion") else None
        diet_id = _name_to_id(payload.get("diet"), "diets", db) if payload.get("diet") else None
        exercise_frequency_id = _name_to_id(payload.get("exercise_frequency"), "exercise_frequencies", db) if payload.get("exercise_frequency") else None
        smoke_frequency_id = _name_to_id(payload.get("smoke_frequency"), "smoke_frequencies", db) if payload.get("smoke_frequency") else None
        drink_frequency_id = _name_to_id(payload.get("drink_frequency"), "drink_frequencies", db) if payload.get("drink_frequency") else None
        sleep_schedule_id = _name_to_id(payload.get("sleep_schedule"), "sleep_schedules", db) if payload.get("sleep_schedule") else None
        
        # drug_use and weed_use: Store enum names directly (not FKs)
        drug_use = payload.get("drug_use")
        weed_use = payload.get("weed_use")

        stmt = text("""
            UPDATE profiles.profiles
            SET
                bio = :bio, drug_use = :drug_use, weed_use = :weed_use,
                gender_id = :gender_id, orientation_id = :orientation_id,
                location = :location, location_label = :location_label,
                show_precise_location = :show_precise_location, pronoun_id = :pronoun_id,
                school = :school, occupation = :occupation, relationship_goal_id = :relationship_goal_id,
                personality_type_id = :personality_type_id, love_language_id = :love_language_id,
                attachment_style_id = :attachment_style_id, political_view_id = :political_view_id,
                zodiac_sign_id = :zodiac_sign_id, religion_id = :religion_id,
                diet_id = :diet_id, exercise_frequency_id = :exercise_frequency_id,
                smoke_frequency_id = :smoke_frequency_id, drink_frequency_id = :drink_frequency_id,
                sleep_schedule_id = :sleep_schedule_id,
                updated_at = now()
            WHERE uid = :uid
        """)

        params = {
            "uid": uid,
            "bio": payload.get("bio"),
            "drug_use": drug_use,
            "weed_use": weed_use,
            "gender_id": gender_id,
            "orientation_id": orientation_id,
            "location": payload.get("location"),
            "location_label": payload.get("location_label"),
            "show_precise_location": payload.get("show_precise_location"),
            "pronoun_id": pronoun_id,
            "school": payload.get("school"),
            "occupation": payload.get("occupation"),
            "relationship_goal_id": relationship_goal_id,
            "personality_type_id": personality_type_id,
            "love_language_id": love_language_id,
            "attachment_style_id": attachment_style_id,
            "political_view_id": political_view_id,
            "zodiac_sign_id": zodiac_sign_id,
            "religion_id": religion_id,
            "diet_id": diet_id,
            "exercise_frequency_id": exercise_frequency_id,
            "smoke_frequency_id": smoke_frequency_id,
            "drink_frequency_id": drink_frequency_id,
            "sleep_schedule_id": sleep_schedule_id,
        }
        
        db.execute(stmt, params)
        
        # Handle junction tables
        _update_junction_table(uid, "interests", "interest_id", payload.get("interests", []), "interests", db)
        _update_junction_table(uid, "pets", "pet_id", payload.get("pets", []), "pets", db)
        _update_junction_table(uid, "languages_spoken", "language_id", payload.get("languages_spoken", []), "languages", db)
        
        db.commit()
        return {"ok": True, "detail": f"Profile for user '{uid}' updated."}
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error during profile update: {e}")