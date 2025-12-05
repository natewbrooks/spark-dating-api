from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

# Enums
from .preferences.genders import GendersEnum
from .preferences.orientation import SexualOrientationsEnum, UpdateSexualOrientationSchema
from .preferences.interests import InterestsEnum 
from .preferences.pronouns import PronounsEnum
from .preferences.relationship_goals import RelationshipGoalsEnum
from .preferences.personality_type import PersonalityTypeEnum
from .preferences.love_language import LoveLanguageEnum
from .preferences.attachment_style import AttachmentStyleEnum
from .preferences.political_views import PoliticalViewsEnum
from .preferences.diet import DietEnum
from .preferences.religion import ReligionEnum
from .preferences.pets import PetsEnum
from .preferences.exercise_frequency import ExerciseFrequencyEnum
from .preferences.drink_frequency import DrinkFrequencyEnum
from .preferences.smoke_frequency import SmokeFrequencyEnum
from .preferences.sleep_schedule import SleepScheduleEnum
from .preferences.zodiac_signs import ZodiacSignsEnum 

class UserProfileSchema(BaseModel):
    created_at: Optional[datetime] = None

    bio: Optional[str] = Field(default=None, max_length=1000)
    drug_use: Optional[bool] = None
    weed_use: Optional[bool] = None

    # These two will need to be converted to their fk UUID by the backend
    gender: Optional[GendersEnum] = None
    orientation: Optional[SexualOrientationsEnum] = None
    interests: List[InterestsEnum] = None
    # # # (e.g. SELECT id FROM public.genders WHERE name = :gender) # # #

    location: Optional[str] = Field(default=None, max_length=255)
    location_label: Optional[str] = Field(default=None, max_length=255)
    show_precise_location: Optional[bool] = None

    pronouns: Optional[PronounsEnum] = None

    languages_spoken: Optional[List[str]] = None

    school: Optional[str] = Field(default=None, max_length=255)
    occupation: Optional[str] = Field(default=None, max_length=255)
    relationship_goal: Optional[RelationshipGoalsEnum] = None

    personality_type: Optional[PersonalityTypeEnum] = None
    love_language: Optional[LoveLanguageEnum] = None
    attachment_style: Optional[AttachmentStyleEnum] = None
    political_view: Optional[PoliticalViewsEnum] = None
    zodiac_sign: Optional[ZodiacSignsEnum] = None
    religion: Optional[ReligionEnum] = None
    diet: Optional[DietEnum] = None
    exercise_frequency: Optional[ExerciseFrequencyEnum] = None

    pets: Optional[List[PetsEnum]] = None

    smoke_frequency: Optional[SmokeFrequencyEnum] = None
    drink_frequency: Optional[DrinkFrequencyEnum] = None
    sleep_schedule: Optional[SleepScheduleEnum] = None
