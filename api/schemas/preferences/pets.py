from enum import Enum


class PetsEnum(str, Enum):
    dogs = "dogs"
    cats = "cats"
    fish = "fish"
    birds = "birds"
    reptiles = "reptiles"
    hamsters = "hamsters"  
    guinea_pigs = "guinea pigs"  
    rabbits = "rabbits"
    none = "none" 
    other = "other"