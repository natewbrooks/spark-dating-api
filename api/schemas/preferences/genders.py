from enum import Enum
from pydantic import BaseModel

class GendersEnum(str, Enum):
    male = "male"
    female = "female"
    nb = "non-binary"
    queer = "genderqueer"
    genderfluid = "genderfluid"
    trans_mtf = "transgender (male to female)"
    trans_ftm = "transgender (female to male)"
    any = "any"

class UpdateGenderSchema(BaseModel):
    gender: GendersEnum