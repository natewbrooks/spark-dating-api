from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from typing import Dict, Any
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

def _get_profile(uid: str, db: Session) -> Dict[str, Any]:
    """
    Retrieves a user's profile and converts foreign key IDs (gender and orientation) 
    to human-readable strings.
    """
    from .gender import _gender_id_to_name 
    from .orientation import _orientation_id_to_name

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

    # Convert Gender ID to Name
    gender_id = profile.get("gender_id")
    if gender_id is not None:
        try:
            gender_name = _gender_id_to_name(id=gender_id, db=db)
            profile["gender"] = gender_name # <-- Add gender name to response
        except HTTPException:
            profile["gender"] = None

    # Convert Orientation ID to Name
    orientation_id = profile.get("orientation_id")
    if orientation_id is not None:
        try:
            orientation_name = _orientation_id_to_name(id=orientation_id, db=db)
            profile["orientation"] = orientation_name # <-- Add orientation name to response
        except HTTPException:
            profile["orientation"] = None

    return profile

def _create_profile(uid: str, payload: UserProfileSchema, db: Session) -> Dict[str, Any]:
    """
    Inserts a new profile record for the user.
    """
    if _profile_exists(uid=uid, db=db): 
        raise HTTPException(status_code=409, detail=f"Profile for user with uid '{uid}' is already created! Use 'PUT' to update it.")

    try:
        from .gender import _gender_name_to_id
        from .interests import _update_profile_interests
        from .orientation import _orientation_name_to_id
    
        _update_profile_interests(payload=payload.get("interests"), uid=uid, db=db)
        gender_id = _gender_name_to_id(name=payload.get("gender"), db=db)
        orientation_id = _orientation_name_to_id(name=payload.get("orientation"), db=db)

        stmt = text("""
        INSERT INTO profiles.profiles (
            uid, bio, drug_use, weed_use, gender_id, orientation_id, 
            location, location_label, show_precise_location, pronouns, 
            languages_spoken, school, occupation, relationship_goal, 
            personality_type, love_language, attachment_style, political_view, 
            zodiac_sign, religion, diet, exercise_frequency, pets, 
            smoke_frequency, drink_frequency, sleep_schedule
        )
        VALUES (
            :uid, :bio, :drug_use, :weed_use, :gender_id, :orientation_id,
            :location, :location_label, :show_precise_location, :pronouns, 
            :languages_spoken, :school, :occupation, :relationship_goal, 
            :personality_type, :love_language, :attachment_style, :political_view, 
            :zodiac_sign, :religion, :diet, :exercise_frequency, :pets, 
            :smoke_frequency, :drink_frequency, :sleep_schedule
        ) RETURNING uid
        """)

        params = {
            "uid": uid,
            "bio": payload.get("bio"),
            "drug_use": payload.get("drug_use"),
            "weed_use": payload.get("weed_use"),
            "gender_id": gender_id,
            "orientation_id": orientation_id,
            "location": payload.get("location"),
            "location_label": payload.get("location_label"),
            "show_precise_location": payload.get("show_precise_location"),
            "pronouns": payload.get("pronouns"),
            "languages_spoken": payload.get("languages_spoken"),
            "school": payload.get("school"),
            "occupation": payload.get("occupation"),
            "relationship_goal": payload.get("relationship_goal"),
            "personality_type": payload.get("personality_type"),
            "love_language": payload.get("love_language"),
            "attachment_style": payload.get("attachment_style"),
            "political_view": payload.get("political_view"),
            "zodiac_sign": payload.get("zodiac_sign"),
            "religion": payload.get("religion"),
            "diet": payload.get("diet"),
            "exercise_frequency": payload.get("exercise_frequency"),
            "pets": payload.get("pets"),
            "smoke_frequency": payload.get("smoke_frequency"),
            "drink_frequency": payload.get("drink_frequency"),
            "sleep_schedule": payload.get("sleep_schedule"),
        }
        
        db.execute(stmt, params)
        return {"ok": True, "detail": f"Profile for user '{uid}' created."}
    
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error during profile creation: {e}")


def _update_profile(uid: str, payload: UserProfileSchema, db: Session) -> Dict[str, Any]:
    """
    Updates an existing profile record for the user.
    """
    if not _profile_exists(uid=uid, db=db):
        # Fallback to creation if profile doesn't exist
        return _create_profile(uid=uid, payload=payload, db=db)
    
    try:
        from .gender import _gender_name_to_id
        from .interests import _update_profile_interests
        from .orientation import _orientation_name_to_id
        
        _update_profile_interests(payload=payload.get("interests"), uid=uid, db=db)
        gender_id = _gender_name_to_id(name=payload.get("gender"), db=db)
        orientation_id = _orientation_name_to_id(name=payload.get("orientation"), db=db)

        stmt = text("""
            UPDATE profiles.profiles
            SET
                bio = :bio, drug_use = :drug_use, weed_use = :weed_use,
                gender_id = :gender_id, orientation_id = :orientation_id,
                location = :location, location_label = :location_label,
                show_precise_location = :show_precise_location, pronouns = :pronouns,
                languages_spoken = :languages_spoken, school = :school,
                occupation = :occupation, relationship_goal = :relationship_goal,
                personality_type = :personality_type, love_language = :love_language,
                attachment_style = :attachment_style, political_view = :political_view,
                zodiac_sign = :zodiac_sign, religion = :religion,
                diet = :diet, exercise_frequency = :exercise_frequency,
                pets = :pets, smoke_frequency = :smoke_frequency,
                drink_frequency = :drink_frequency, sleep_schedule = :sleep_schedule,
                updated_at = now()
            WHERE uid = :uid
        """)

        params = {
            "uid": uid,
            "bio": payload.get("bio"),
            "drug_use": payload.get("drug_use"),
            "weed_use": payload.get("weed_use"),
            "gender_id": gender_id,
            "orientation_id": orientation_id,
            "location": payload.get("location"),
            "location_label": payload.get("location_label"),
            "show_precise_location": payload.get("show_precise_location"),
            "pronouns": payload.get("pronouns"),
            "languages_spoken": payload.get("languages_spoken"),
            "school": payload.get("school"),
            "occupation": payload.get("occupation"),
            "relationship_goal": payload.get("relationship_goal"),
            "personality_type": payload.get("personality_type"),
            "love_language": payload.get("love_language"),
            "attachment_style": payload.get("attachment_style"),
            "political_view": payload.get("political_view"),
            "zodiac_sign": payload.get("zodiac_sign"),
            "religion": payload.get("religion"),
            "diet": payload.get("diet"),
            "exercise_frequency": payload.get("exercise_frequency"),
            "pets": payload.get("pets"),
            "smoke_frequency": payload.get("smoke_frequency"),
            "drink_frequency": payload.get("drink_frequency"),
            "sleep_schedule": payload.get("sleep_schedule"),
        }
        
        db.execute(stmt, params)
        return {"ok": True, "detail": f"Profile for user '{uid}' updated."}
        
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error during profile update: {e}")