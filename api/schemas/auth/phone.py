from pydantic import BaseModel, field_validator
import re

class PhoneOTPAnswerSchema(BaseModel):
    phone: str
    code: str
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Remove non-digit characters (including spaces, dashes, parentheses)
        cleaned = re.sub(r'\D', '', v)
        
        # Check length and format based on US/Canada assumption
        # 10 digits (e.g., 5551234567)
        if len(cleaned) == 10:
            final_phone = f'+1{cleaned}'
        
        # 11 digits starting with 1 (e.g., 15551234567)
        elif len(cleaned) == 11 and cleaned.startswith('1'):
            final_phone = f'+{cleaned}'
            
        # 12 digits starting with +1 (e.g., +15551234567 - digits only means it's 12 chars if we ignore the '+' which we removed)
        # This case is redundant if the above checks pass, but catches numbers that started with '+' but maybe had 11 digits after cleanup.
        elif len(cleaned) == 11 and not cleaned.startswith('1'):
             # This handles cases like if the user input "+5551234567" which is invalid for our region.
             raise ValueError('Phone must be a valid 10-digit number or 11 digits starting with 1.')

        else:
            raise ValueError('Phone must be a valid 10-digit number or 11 digits starting with 1.')
        
        # The returned value is the clean E.164 string (e.g., '+15551234567')
        return final_phone