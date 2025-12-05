from enum import Enum

class DrinkFrequencyEnum(str, Enum):
    never = "never"
    occasionally = "occasionally"
    socially = "socially"
    often = "often"
