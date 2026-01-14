import os
from typing import Optional

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/voice_intake")
    
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
    
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    
    GOOGLE_CALENDAR_CREDENTIALS: str = os.getenv("GOOGLE_CALENDAR_CREDENTIALS", "")
    GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    
    _sender_email = os.getenv("SENDER_EMAIL") or os.getenv("GMAIL_USER") or ""
    _sender_password = os.getenv("SENDER_PASSWORD") or os.getenv("GMAIL_PASSWORD") or ""
    
    SENDER_EMAIL: str = _sender_email
    SENDER_PASSWORD: str = _sender_password
    SENDER_NAME: str = os.getenv("SENDER_NAME", "Legal Intake Team")
    GMAIL_USER: str = _sender_email
    GMAIL_PASSWORD: str = _sender_password
    
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    def validate_email_config(self) -> bool:
        required_vars = {
            "SENDER_EMAIL": self.SENDER_EMAIL,
            "SENDER_PASSWORD": self.SENDER_PASSWORD
        }
        missing = [key for key, value in required_vars.items() if not value]
        if missing:
            return False
        return True

settings = Settings()

