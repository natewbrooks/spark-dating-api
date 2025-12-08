from enum import Enum

class DrugUseFrequencyEnum(str, Enum):
    never = "never"
    occasionally = "occasionally"
    socially = "socially"
    often = "often"
