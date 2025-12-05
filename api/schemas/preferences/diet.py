from enum import Enum

class DietEnum(str, Enum):
    omnivore = "omnivore"
    pescetarian = "pescetarian"
    vegetarian = "vegetarian"
    vegan = "vegan"
    flexitarian = "flexitarian"