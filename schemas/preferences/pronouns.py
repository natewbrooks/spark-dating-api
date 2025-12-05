from enum import Enum

class PronounsEnum(str, Enum):
    she_her = "she/her"
    he_him = "he/him"
    they_them = "they/them"
    any = "any"
    ask_me = "ask me"