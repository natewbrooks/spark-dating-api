from enum import Enum

class ExerciseFrequencyEnum(str, Enum):
    everyday = "everyday"
    often = "often"
    sometimes = "sometimes"
    never = "never"