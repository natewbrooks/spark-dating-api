from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.db import get_db
from middleware.auth import auth_user
from typing import List, Any, Annotated

from controllers.profile_options import dispatch_preference_action

from schemas.preferences import (
    AttachmentStyleEnum, DietEnum, DrinkFrequencyEnum, ExerciseFrequencyEnum, 
    LoveLanguageEnum, PersonalityTypeEnum, PetsEnum, PoliticalViewsEnum, 
    PronounsEnum, RelationshipGoalsEnum, ReligionEnum, SleepScheduleEnum, 
    SmokeFrequencyEnum, ZodiacSignsEnum, InterestsEnum, GendersEnum, LanguageEnum
)

from schemas.preferences.sexual_orientation import SexualOrientationsEnum


router = APIRouter(prefix="", tags=["Profile: Preferences & Identity"])


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_all_options_for_table(table_name: str, db: Session):
    """Generic function to get all options from a lookup table."""
    stmt = text(f"SELECT id, name FROM public.{table_name} ORDER BY name")
    result = db.execute(stmt).mappings().all()
    return [{"id": row["id"], "name": row["name"]} for row in result]


# ==============================================================================
# A. PUBLIC ENDPOINTS: Get all available options for each preference type
# ==============================================================================

@router.get("/genders", summary="Get All Gender Options")
def get_all_genders(db: Annotated[Session, Depends(get_db)]):
    """Returns all available gender options."""
    return get_all_options_for_table("genders", db)

@router.get("/relationship-goals", summary="Get All Relationship Goal Options")
def get_all_relationship_goals(db: Annotated[Session, Depends(get_db)]):
    """Returns all available relationship goal options."""
    return get_all_options_for_table("relationship_goals", db)

@router.get("/interests", summary="Get All Interest Options")
def get_all_interests(db: Annotated[Session, Depends(get_db)]):
    """Returns all available interest options."""
    return get_all_options_for_table("interests", db)

@router.get("/personality-types", summary="Get All Personality Type Options")
def get_all_personality_types(db: Annotated[Session, Depends(get_db)]):
    """Returns all available personality type options."""
    return get_all_options_for_table("personality_types", db)

@router.get("/love-languages", summary="Get All Love Language Options")
def get_all_love_languages(db: Annotated[Session, Depends(get_db)]):
    """Returns all available love language options."""
    return get_all_options_for_table("love_languages", db)

@router.get("/languages", summary="Get All Language Options")
def get_all_languages(db: Annotated[Session, Depends(get_db)]):
    """Returns all available language options."""
    return get_all_options_for_table("languages", db)

@router.get("/attachment-styles", summary="Get All Attachment Style Options")
def get_all_attachment_styles(db: Annotated[Session, Depends(get_db)]):
    """Returns all available attachment style options."""
    return get_all_options_for_table("attachment_styles", db)

@router.get("/political-views", summary="Get All Political View Options")
def get_all_political_views(db: Annotated[Session, Depends(get_db)]):
    """Returns all available political view options."""
    return get_all_options_for_table("political_views", db)

@router.get("/zodiac-signs", summary="Get All Zodiac Sign Options")
def get_all_zodiac_signs(db: Annotated[Session, Depends(get_db)]):
    """Returns all available zodiac sign options."""
    return get_all_options_for_table("zodiac_signs", db)

@router.get("/religions", summary="Get All Religion Options")
def get_all_religions(db: Annotated[Session, Depends(get_db)]):
    """Returns all available religion options."""
    return get_all_options_for_table("religions", db)

@router.get("/diets", summary="Get All Diet Options")
def get_all_diets(db: Annotated[Session, Depends(get_db)]):
    """Returns all available diet options."""
    return get_all_options_for_table("diets", db)

@router.get("/exercise-frequencies", summary="Get All Exercise Frequency Options")
def get_all_exercise_frequencies(db: Annotated[Session, Depends(get_db)]):
    """Returns all available exercise frequency options."""
    return get_all_options_for_table("exercise_frequencies", db)

@router.get("/pets", summary="Get All Pet Options")
def get_all_pets(db: Annotated[Session, Depends(get_db)]):
    """Returns all available pet options."""
    return get_all_options_for_table("pets", db)

@router.get("/smoke-frequencies", summary="Get All Smoke Frequency Options")
def get_all_smoke_frequencies(db: Annotated[Session, Depends(get_db)]):
    """Returns all available smoke frequency options."""
    return get_all_options_for_table("smoke_frequencies", db)

@router.get("/drink-frequencies", summary="Get All Drink Frequency Options")
def get_all_drink_frequencies(db: Annotated[Session, Depends(get_db)]):
    """Returns all available drink frequency options."""
    return get_all_options_for_table("drink_frequencies", db)

@router.get("/sleep-schedules", summary="Get All Sleep Schedule Options")
def get_all_sleep_schedules(db: Annotated[Session, Depends(get_db)]):
    """Returns all available sleep schedule options."""
    return get_all_options_for_table("sleep_schedules", db)

@router.get("/pronouns", summary="Get All Pronoun Options")
def get_all_pronouns(db: Annotated[Session, Depends(get_db)]):
    """Returns all available pronoun options."""
    return get_all_options_for_table("pronouns", db)

@router.get("/orientations", summary="Get All Sexual Orientation Options")
def get_all_orientations(db: Annotated[Session, Depends(get_db)]):
    """Returns all available sexual orientation options."""
    return get_all_options_for_table("orientations", db)



# ==============================================================================
# C. SELF UPDATE/DELETE ENDPOINTS: Manage logged-in user's preferences
# ==============================================================================

# --- TARGET GENDER (Match Preference) ---
@router.post("/me/target-gender", summary="Update My Target Gender Preference")
def update_my_target_gender(
    payload: GendersEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your preferred target gender for matching."""
    return dispatch_preference_action("update", "target_gender", uid, db, payload)

# --- RELATIONSHIP GOAL ---
@router.post("/me/relationship-goal", summary="Update My Relationship Goal")
def update_my_relationship_goal(
    payload: RelationshipGoalsEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your relationship goal."""
    return dispatch_preference_action("update", "relationship_goals", uid, db, payload)

@router.delete("/me/relationship-goal", summary="Clear My Relationship Goal")
def delete_my_relationship_goal(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your relationship goal."""
    return dispatch_preference_action("delete", "relationship_goals", uid, db)

# --- INTERESTS (Multi-value) ---
@router.post("/me/interests", summary="Update My Interests")
def update_my_interests(
    payload: List[InterestsEnum], 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Replaces your interests list."""
    return dispatch_preference_action("update", "interests", uid, db, payload)

@router.delete("/me/interests", summary="Clear My Interests")
def delete_my_interests(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears all your interests."""
    return dispatch_preference_action("delete", "interests", uid, db)

# --- PERSONALITY TYPE ---
@router.post("/me/personality-type", summary="Update My Personality Type")
def update_my_personality_type(
    payload: PersonalityTypeEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your personality type."""
    return dispatch_preference_action("update", "personality_types", uid, db, payload)

@router.delete("/me/personality-type", summary="Clear My Personality Type")
def delete_my_personality_type(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your personality type."""
    return dispatch_preference_action("delete", "personality_types", uid, db)

# --- LOVE LANGUAGE ---
@router.post("/me/love-language", summary="Update My Love Language")
def update_my_love_language(
    payload: LoveLanguageEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your love language."""
    return dispatch_preference_action("update", "love_languages", uid, db, payload)

@router.delete("/me/love-language", summary="Clear My Love Language")
def delete_my_love_language(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your love language."""
    return dispatch_preference_action("delete", "love_languages", uid, db)

# --- LANGUAGE ---
@router.post("/me/languages-spoken", summary="Update My Spoken Languages")
def update_my_languages(
    payload: List[LanguageEnum], 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your spoken languages."""
    return dispatch_preference_action("update", "languages_spoken", uid, db, payload)

@router.delete("/me/languages", summary="Clear My Spoken Languages")
def delete_my_languages(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your spoken languages."""
    return dispatch_preference_action("delete", "languages_spoken", uid, db)

# --- ATTACHMENT STYLE ---
@router.post("/me/attachment-style", summary="Update My Attachment Style")
def update_my_attachment_style(
    payload: AttachmentStyleEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your attachment style."""
    return dispatch_preference_action("update", "attachment_styles", uid, db, payload)

@router.delete("/me/attachment-style", summary="Clear My Attachment Style")
def delete_my_attachment_style(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your attachment style."""
    return dispatch_preference_action("delete", "attachment_styles", uid, db)

# --- POLITICAL VIEW ---
@router.post("/me/political-view", summary="Update My Political View")
def update_my_political_view(
    payload: PoliticalViewsEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your political view."""
    return dispatch_preference_action("update", "political_views", uid, db, payload)

@router.delete("/me/political-view", summary="Clear My Political View")
def delete_my_political_view(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your political view."""
    return dispatch_preference_action("delete", "political_views", uid, db)

# --- ZODIAC SIGN ---
@router.post("/me/zodiac-sign", summary="Update My Zodiac Sign")
def update_my_zodiac_sign(
    payload: ZodiacSignsEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your zodiac sign."""
    return dispatch_preference_action("update", "zodiac_signs", uid, db, payload)

@router.delete("/me/zodiac-sign", summary="Clear My Zodiac Sign")
def delete_my_zodiac_sign(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your zodiac sign."""
    return dispatch_preference_action("delete", "zodiac_signs", uid, db)

# --- RELIGION ---
@router.post("/me/religion", summary="Update My Religion")
def update_my_religion(
    payload: ReligionEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your religion."""
    return dispatch_preference_action("update", "religions", uid, db, payload)

@router.delete("/me/religion", summary="Clear My Religion")
def delete_my_religion(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your religion."""
    return dispatch_preference_action("delete", "religions", uid, db)

# --- DIET ---
@router.post("/me/diet", summary="Update My Diet")
def update_my_diet(
    payload: DietEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your diet preference."""
    return dispatch_preference_action("update", "diets", uid, db, payload)

@router.delete("/me/diet", summary="Clear My Diet")
def delete_my_diet(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your diet preference."""
    return dispatch_preference_action("delete", "diets", uid, db)

# --- EXERCISE FREQUENCY ---
@router.post("/me/exercise-frequency", summary="Update My Exercise Frequency")
def update_my_exercise_frequency(
    payload: ExerciseFrequencyEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your exercise frequency."""
    return dispatch_preference_action("update", "exercise_frequencies", uid, db, payload)

@router.delete("/me/exercise-frequency", summary="Clear My Exercise Frequency")
def delete_my_exercise_frequency(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your exercise frequency."""
    return dispatch_preference_action("delete", "exercise_frequencies", uid, db)

# --- PETS (Multi-value) ---
@router.post("/me/pets", summary="Update My Pet Preferences")
def update_my_pets(
    payload: List[PetsEnum], 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Replaces your pet preferences list."""
    return dispatch_preference_action("update", "pets", uid, db, payload)

@router.delete("/me/pets", summary="Clear My Pet Preferences")
def delete_my_pets(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears all your pet preferences."""
    return dispatch_preference_action("delete", "pets", uid, db)

# --- SMOKE FREQUENCY ---
@router.post("/me/smoke-frequency", summary="Update My Smoke Frequency")
def update_my_smoke_frequency(
    payload: SmokeFrequencyEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your smoke frequency."""
    return dispatch_preference_action("update", "smoke_frequencies", uid, db, payload)

@router.delete("/me/smoke-frequency", summary="Clear My Smoke Frequency")
def delete_my_smoke_frequency(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your smoke frequency."""
    return dispatch_preference_action("delete", "smoke_frequencies", uid, db)

# --- DRINK FREQUENCY ---
@router.post("/me/drink-frequency", summary="Update My Drink Frequency")
def update_my_drink_frequency(
    payload: DrinkFrequencyEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your drink frequency."""
    return dispatch_preference_action("update", "drink_frequencies", uid, db, payload)

@router.delete("/me/drink-frequency", summary="Clear My Drink Frequency")
def delete_my_drink_frequency(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your drink frequency."""
    return dispatch_preference_action("delete", "drink_frequencies", uid, db)

# --- SLEEP SCHEDULE ---
@router.post("/me/sleep-schedule", summary="Update My Sleep Schedule")
def update_my_sleep_schedule(
    payload: SleepScheduleEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your sleep schedule."""
    return dispatch_preference_action("update", "sleep_schedules", uid, db, payload)

@router.delete("/me/sleep-schedule", summary="Clear My Sleep Schedule")
def delete_my_sleep_schedule(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your sleep schedule."""
    return dispatch_preference_action("delete", "sleep_schedules", uid, db)

# --- PRONOUNS ---
@router.post("/me/pronoun", summary="Update My Pronouns")
def update_my_pronoun(
    payload: PronounsEnum, 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Sets your pronouns."""
    return dispatch_preference_action("update", "pronouns", uid, db, payload)

@router.delete("/me/pronoun", summary="Clear My Pronouns")
def delete_my_pronoun(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears your pronouns."""
    return dispatch_preference_action("delete", "pronouns", uid, db)

# --- SEXUAL ORIENTATIONS (Multi-value) ---
@router.post("/me/sexual-orientations", summary="Update My Sexual Orientations")
def update_my_sexual_orientations(
    payload: List[SexualOrientationsEnum], 
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Replaces your sexual orientations list."""
    return dispatch_preference_action("update", "sexual_orientations", uid, db, payload)

@router.delete("/me/sexual-orientations", summary="Clear My Sexual Orientations")
def delete_my_sexual_orientations(
    uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Clears all your sexual orientations."""
    return dispatch_preference_action("delete", "sexual_orientations", uid, db)

# ==============================================================================
# D. SELF GET ENDPOINTS: Read logged-in user's preferences/identity fields
# ==============================================================================

@router.get("/me/target-gender", summary="Get My Target Gender Preference")
def get_my_target_gender(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your preferred target gender for matching."""
    return dispatch_preference_action("get", "target_gender", uid, db)


@router.get("/me/relationship-goal", summary="Get My Relationship Goal")
def get_my_relationship_goal(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your relationship goal."""
    return dispatch_preference_action("get", "relationship_goals", uid, db)


@router.get("/me/interests", summary="Get My Interests")
def get_my_interests(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your list of interests."""
    return dispatch_preference_action("get", "interests", uid, db)


@router.get("/me/personality-type", summary="Get My Personality Type")
def get_my_personality_type(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your personality type."""
    return dispatch_preference_action("get", "personality_types", uid, db)


@router.get("/me/love-language", summary="Get My Love Language")
def get_my_love_language(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your love language."""
    return dispatch_preference_action("get", "love_languages", uid, db)


@router.get("/me/languages-spoken", summary="Get My Languages")
def get_my_languages_spoen(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your languages."""
    return dispatch_preference_action("get", "languages_spoken", uid, db)


@router.get("/me/attachment-style", summary="Get My Attachment Style")
def get_my_attachment_style(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your attachment style."""
    return dispatch_preference_action("get", "attachment_styles", uid, db)


@router.get("/me/political-view", summary="Get My Political View")
def get_my_political_view(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your political view."""
    return dispatch_preference_action("get", "political_views", uid, db)


@router.get("/me/zodiac-sign", summary="Get My Zodiac Sign")
def get_my_zodiac_sign(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your zodiac sign."""
    return dispatch_preference_action("get", "zodiac_signs", uid, db)


@router.get("/me/religion", summary="Get My Religion")
def get_my_religion(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your religion."""
    return dispatch_preference_action("get", "religions", uid, db)


@router.get("/me/diet", summary="Get My Diet")
def get_my_diet(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your diet preference."""
    return dispatch_preference_action("get", "diets", uid, db)


@router.get("/me/exercise-frequency", summary="Get My Exercise Frequency")
def get_my_exercise_frequency(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your exercise frequency."""
    return dispatch_preference_action("get", "exercise_frequencies", uid, db)


@router.get("/me/pets", summary="Get My Pet Preferences")
def get_my_pets(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your pet preferences."""
    return dispatch_preference_action("get", "pets", uid, db)


@router.get("/me/smoke-frequency", summary="Get My Smoke Frequency")
def get_my_smoke_frequency(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your smoke frequency."""
    return dispatch_preference_action("get", "smoke_frequencies", uid, db)


@router.get("/me/drink-frequency", summary="Get My Drink Frequency")
def get_my_drink_frequency(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your drink frequency."""
    return dispatch_preference_action("get", "drink_frequencies", uid, db)


@router.get("/me/sleep-schedule", summary="Get My Sleep Schedule")
def get_my_sleep_schedule(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your sleep schedule."""
    return dispatch_preference_action("get", "sleep_schedules", uid, db)


@router.get("/me/pronoun", summary="Get My Pronouns")
def get_my_pronoun(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your pronouns."""
    return dispatch_preference_action("get", "pronouns", uid, db)


@router.get("/me/sexual-orientations", summary="Get My Sexual Orientations")
def get_my_sexual_orientations(
    uid: Annotated[str, Depends(auth_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Returns your sexual orientations."""
    return dispatch_preference_action("get", "sexual_orientations", uid, db)



# ==============================================================================
# B. USER-SPECIFIC GET ENDPOINTS: Get another user's preferences
# ==============================================================================

@router.get("/{target_uid}/target-gender", summary="Get User's Target Gender Preference")
def get_user_target_gender(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's preferred target gender for matching."""
    return dispatch_preference_action("get", "target_gender", target_uid, db)

@router.get("/{target_uid}/relationship-goals", summary="Get User's Relationship Goal")
def get_user_relationship_goals(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's relationship goal."""
    return dispatch_preference_action("get", "relationship_goals", target_uid, db)

@router.get("/{target_uid}/interests", summary="Get User's Interests")
def get_user_interests(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's list of interests."""
    return dispatch_preference_action("get", "interests", target_uid, db)

@router.get("/{target_uid}/personality-types", summary="Get User's Personality Type")
def get_user_personality_types(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's personality type."""
    return dispatch_preference_action("get", "personality_types", target_uid, db)

@router.get("/{target_uid}/love-languages", summary="Get User's Love Language")
def get_user_love_languages(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's love language."""
    return dispatch_preference_action("get", "love_languages", target_uid, db)

@router.get("/{target_uid}/languages-spoken", summary="Get User's Spoken Languages")
def get_user_languages(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's spoken languages."""
    return dispatch_preference_action("get", "languages_spoken", target_uid, db)


@router.get("/{target_uid}/attachment-styles", summary="Get User's Attachment Style")
def get_user_attachment_styles(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's attachment style."""
    return dispatch_preference_action("get", "attachment_styles", target_uid, db)

@router.get("/{target_uid}/political-views", summary="Get User's Political View")
def get_user_political_views(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's political view."""
    return dispatch_preference_action("get", "political_views", target_uid, db)

@router.get("/{target_uid}/zodiac-signs", summary="Get User's Zodiac Sign")
def get_user_zodiac_signs(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's zodiac sign."""
    return dispatch_preference_action("get", "zodiac_signs", target_uid, db)

@router.get("/{target_uid}/religions", summary="Get User's Religion")
def get_user_religions(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's religion."""
    return dispatch_preference_action("get", "religions", target_uid, db)

@router.get("/{target_uid}/diets", summary="Get User's Diet")
def get_user_diets(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's diet preference."""
    return dispatch_preference_action("get", "diets", target_uid, db)

@router.get("/{target_uid}/exercise-frequencies", summary="Get User's Exercise Frequency")
def get_user_exercise_frequencies(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's exercise frequency."""
    return dispatch_preference_action("get", "exercise_frequencies", target_uid, db)

@router.get("/{target_uid}/pets", summary="Get User's Pet Preferences")
def get_user_pets(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's pet preferences."""
    return dispatch_preference_action("get", "pets", target_uid, db)

@router.get("/{target_uid}/smoke-frequencies", summary="Get User's Smoke Frequency")
def get_user_smoke_frequencies(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's smoke frequency."""
    return dispatch_preference_action("get", "smoke_frequencies", target_uid, db)

@router.get("/{target_uid}/drink-frequencies", summary="Get User's Drink Frequency")
def get_user_drink_frequencies(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's drink frequency."""
    return dispatch_preference_action("get", "drink_frequencies", target_uid, db)

@router.get("/{target_uid}/sleep-schedules", summary="Get User's Sleep Schedule")
def get_user_sleep_schedules(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's sleep schedule."""
    return dispatch_preference_action("get", "sleep_schedules", target_uid, db)

@router.get("/{target_uid}/pronouns", summary="Get User's Pronouns")
def get_user_pronouns(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's preferred pronouns."""
    return dispatch_preference_action("get", "pronouns", target_uid, db)

@router.get("/{target_uid}/sexual-orientations", summary="Get User's Sexual Orientations")
def get_user_sexual_orientations(
    target_uid: str, 
    caller_uid: Annotated[str, Depends(auth_user)], 
    db: Annotated[Session, Depends(get_db)]
):
    """Returns a user's sexual orientations."""
    return dispatch_preference_action("get", "sexual_orientations", target_uid, db)
