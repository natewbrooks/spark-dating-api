from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field

from .genders import GendersEnum, UpdateGenderSchema
from .interests import InterestsEnum 
from .pronouns import PronounsEnum
from .relationship_goals import RelationshipGoalsEnum
from .personality_type import PersonalityTypeEnum
from .love_language import LoveLanguageEnum
from .attachment_style import AttachmentStyleEnum
from .political_views import PoliticalViewsEnum
from .diet import DietEnum
from .religion import ReligionEnum
from .pets import PetsEnum
from .exercise_frequency import ExerciseFrequencyEnum
from .drink_frequency import DrinkFrequencyEnum
from .smoke_frequency import SmokeFrequencyEnum
from .sleep_schedule import SleepScheduleEnum
from .zodiac_signs import ZodiacSignsEnum 
from .languages import LanguageEnum

# Mirror the settings in profiles.profiles table
class ExtraPreferenceOptionsSchema(BaseModel):
    school: Optional[str] = None
    drug_use: Optional[List[SmokeFrequencyEnum]] = None
    weed_use: Optional[List[SmokeFrequencyEnum]] = None

    relationship_goal: Optional[List[RelationshipGoalsEnum]] = None
    interests: Optional[List[InterestsEnum]] = None
    personality_type: Optional[List[PersonalityTypeEnum]] = None
    love_language: Optional[List[LoveLanguageEnum]] = None
    languages_spoken: Optional[List[LanguageEnum]] = None

    attachment_style: Optional[List[AttachmentStyleEnum]] = None
    political_view: Optional[List[PoliticalViewsEnum]] = None
    zodiac_sign: Optional[List[ZodiacSignsEnum]] = None
    religion: Optional[List[ReligionEnum]] = None
    diet: Optional[List[DietEnum]] = None

    exercise_frequency: Optional[List[ExerciseFrequencyEnum]] = None
    pets: Optional[List[PetsEnum]] = None
    smoke_frequency: Optional[List[SmokeFrequencyEnum]] = None
    drink_frequency: Optional[List[DrinkFrequencyEnum]] = None
    sleep_schedule: Optional[List[SleepScheduleEnum]] = None


class UserProfilePreferencesSchema(BaseModel):
    target_gender: GendersEnum = GendersEnum.any
    age_min: int = 18
    age_max: int = 70
    max_distance: int = 50
    extra_options: Optional[ExtraPreferenceOptionsSchema] = None

__all__ = ["ExtraPreferenceOptionsSchema", "UserProfilePreferencesSchema"]