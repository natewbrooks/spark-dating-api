from .supabase import supabase_for_service as supabase
import re

"""
THIS FILE HANDLES THE INTERACTIONS WITH SUPABASE AUTHENTICATION. 
THIS IS PROVIDER AGNOSTIC, BUT JUST FOR CLARITY WE ARE USING 'TWILIO AUTH'

THE MAIN PURPOSE OF THIS FILE IS TO BE OF SERVICE TO THE 'routers.auth' API ENDPOINTS AND 
OTP (ONE TIME PASSWORD) ACTS AS OUR ONLY METHOD OF VERIFICATION FOR USERS CURRENTLY.
"""

# The E.164 regex still requires the +1 prefix for validation, which is fine.
E164 = re.compile(r"^\+[1-9]\d{7,14}$")  # strict E.164

def is_valid_phone(phone: str) -> bool:
    """Checks if the phone number is in strict E.164 format (e.g., +15551234567)."""
    return bool(E164.match(phone.strip()))

def _format_phone_for_e164(phone: str) -> str:
    """Ensures the phone number is prefixed with '+1' if it is a standard 10-digit number."""
    # Clean up input by removing non-digit characters and spaces, then strip whitespace
    cleaned_phone = re.sub(r'\D', '', phone).strip()

    # If the number already starts with '1', ensure it has a '+' (e.g., '12015550123')
    if cleaned_phone.startswith('1') and len(cleaned_phone) == 11:
        return f'+{cleaned_phone}'
        
    # If the number is 10 digits (e.g., '2015550123'), prepend '+1'
    if len(cleaned_phone) == 10:
        return f'+1{cleaned_phone}'
    
    # Otherwise, return the cleaned phone number (will fail is_valid_phone if not already E.164)
    return cleaned_phone

def send_otp(phone: str):
    # Format the input phone number to include the '+1' prefix if necessary
    e164_phone = _format_phone_for_e164(phone)

    # Validate the newly formatted phone number
    if not is_valid_phone(e164_phone):
        raise ValueError("Phone number is invalid. It must be a 10-digit US/Canada number or full E.164 format.")

    print(is_valid_phone(e164_phone))
    
    # Use the validated, formatted E.164 number for Supabase
    return supabase.auth.sign_in_with_otp({
      'phone': e164_phone,
    })

def verify_otp(phone: str, code: int):
    # Format the input phone number to include the '+1' prefix if necessary
    e164_phone = _format_phone_for_e164(phone)
    
    # Validate the phone number
    if not is_valid_phone(e164_phone):
        raise ValueError("Phone number is invalid. It must be a 10-digit US/Canada number or full E.164 format.")
        
    # Validate the OTP code
    if not code or not str(code).isdigit():
        raise ValueError("OTP must be numeric")

    # Use the validated, formatted E.164 number for Supabase
    return supabase.auth.verify_otp({
      'phone': e164_phone,
      'token': str(code), # code should be passed as a string/token
      'type': 'sms',
    })