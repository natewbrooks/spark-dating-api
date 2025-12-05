from enum import Enum

class SmokeFrequencyEnum(str, Enum):
    never = "never"
    occasionally = "occasionally"
    socially = "socially"
    often = "often"
