from enum import Enum

class SleepScheduleEnum(str, Enum):
    early_bird = "early_bird"
    night_owl = "night_owl"
    flexible = "flexible"
    irregular = "irregular"
