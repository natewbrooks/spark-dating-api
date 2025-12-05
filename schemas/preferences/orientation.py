from enum import Enum
from pydantic import BaseModel

class SexualOrientationsEnum(str, Enum):
    straight = "straight" # Attraction to the opposite gender
    gay = "gay" # Same-gender attraction (commonly men)
    lesbian = "lesbian" # Same-gender attraction (commonly women)
    bisexual = "bisexual" # Attraction to more than one gender
    pansexual = "pansexual" # Attraction regardless of gender
    asexual = "asexual" # Lack of sexual attraction
    demisexual = "demisexual" # Attraction develops after emotional bond
    queer = "queer" # Broad, non-specific orientation identity
    questioning = "questioning" # Still exploring orientation
    omnisexual = "omnisexual" # Attraction to all genders, gender is a factor
    sapiosexual = "sapiosexual" # Attraction based on intelligence
    graysexual = "graysexual" # Occasional or limited sexual attraction
    heteroflexible = "heteroflexible" # Primarily straight, occasional same-sex attraction
    homoflexible = "homoflexible" # Primarily gay/lesbian, occasional opposite-sex attraction
    skoliosexual = "skoliosexual" # Attraction to nonbinary or gender-nonconforming people

class UpdateSexualOrientationSchema(BaseModel):
    orientation: SexualOrientationsEnum