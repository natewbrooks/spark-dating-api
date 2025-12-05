from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import get_db
from middleware.auth import auth_user

from schemas.profile import UserProfileSchema

from .gender import _gender_name_to_id
from .orientation import _orientation_name_to_id
from .interests import _update_profile_interests

from controllers.profile import _profile_exists, _get_profile

router = APIRouter(prefix='/me')

@router.get("")
def get_my_profile(uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    return _get_profile(uid=uid, db=db)

"""Used the first time after a user registers, to create their dating profile"""
@router.post("")
def create_profile(payload: UserProfileSchema, uid: str = Depends(auth_user), db: Session = Depends(get_db)):
    payload = jsonable_encoder(payload)
    if _profile_exists(uid=uid, db=db): 
        raise HTTPException(status_code=409, detail=f"Profile for user with uid '{uid}' is already created! Use 'PUT' to update it.")

    _update_profile_interests(payload=payload.get("interests"), uid=uid, db=db)
    gender_id = _gender_name_to_id(name=payload.get("gender"), db=db)
    orientation_id = _orientation_name_to_id(name=payload.get("orientation"), db=db)

    # Not finished with this
    stmt = text("""
    INSERT INTO profiles.profiles (
        uid,
        bio,
        drug_use,
        weed_use,
        gender_id,
        orientation_id,
        location,
        location_label,
        show_precise_location,
        pronouns,
        languages_spoken,
        school,
        occupation,
        relationship_goal,
        personality_type,
        love_language,
        attachment_style,
        political_view,
        zodiac_sign,
        religion,
        diet,
        exercise_frequency,
        pets,
        smoke_frequency,
        drink_frequency,
        sleep_schedule
    )
    VALUES (
        :uid,
        :bio,
        :drug_use,
        :weed_use,
        :gender_id,
        :orientation_id,
        :location,
        :location_label,
        :show_precise_location,
        :pronouns,
        :languages_spoken,
        :school,
        :occupation,
        :relationship_goal,
        :personality_type,
        :love_language,
        :attachment_style,
        :political_view,
        :zodiac_sign,
        :religion,
        :diet,
        :exercise_frequency,
        :pets,
        :smoke_frequency,
        :drink_frequency,
        :sleep_schedule
        )
    """)

    db.execute(
        stmt,
        {
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
        },
    )

"""Used to update a user's profile information"""
@router.put("")
def update_profile(
    payload: UserProfileSchema,
    uid: str = Depends(auth_user),
    db: Session = Depends(get_db),
):
    # Create profile for them automatically
    if not _profile_exists(uid=uid, db=db):
        return create_profile(payload=payload, uid=uid, db=db)
        # raise HTTPException(status_code=404, detail=f"User with id '{uid}' does not exist!")

    payload = jsonable_encoder(payload)
    _update_profile_interests(payload=payload.get("interests"), uid=uid, db=db)
    gender_id = _gender_name_to_id(name=payload.get("gender"), db=db)
    orientation_id = _orientation_name_to_id(name=payload.get("orientation"), db=db)

    stmt = text("""
        UPDATE profiles.profiles
        SET
            bio = :bio,
            drug_use = :drug_use,
            weed_use = :weed_use,
            gender_id = :gender_id,
            orientation_id = :orientation_id,
            location = :location,
            location_label = :location_label,
            show_precise_location = :show_precise_location,
            pronouns = :pronouns,
            languages_spoken = :languages_spoken,
            school = :school,
            occupation = :occupation,
            relationship_goal = :relationship_goal,
            personality_type = :personality_type,
            love_language = :love_language,
            attachment_style = :attachment_style,
            political_view = :political_view,
            zodiac_sign = :zodiac_sign,
            religion = :religion,
            diet = :diet,
            exercise_frequency = :exercise_frequency,
            pets = :pets,
            smoke_frequency = :smoke_frequency,
            drink_frequency = :drink_frequency,
            sleep_schedule = :sleep_schedule,
            updated_at = now()
        WHERE uid = :uid
    """)

    db.execute(
        stmt,
        {
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
        },
    )

    return {"ok": True, "detail": f"Profile for user '{uid}' updated."}
