from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Google OAuth credentials
    GOOGLE_CLIENT_ID: Optional[str]
    GOOGLE_CLIENT_SECRET: Optional[str]
    GOOGLE_REDIRECT_URI: Optional[str]
    GOOGLE_TOKEN_URL: str = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL: str = 'https://www.googleapis.com/oauth2/v1/userinfo'
    GOOGLE_AUTH_URL: str = 'https://accounts.google.com/o/oauth2/v2/auth'

    # Microsoft OAuth credentials
    MICROSOFT_CLIENT_ID: Optional[str]
    MICROSOFT_CLIENT_SECRET: Optional[str]
    MICROSOFT_REDIRECT_URI: Optional[str]
    MICROSOFT_TOKEN_URL: str = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    MICROSOFT_USERINFO_URL: str = 'https://graph.microsoft.com/v1.0/me'
    MICROSOFT_AUTH_URL: str = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'

    # API key for external services
    API_KEY: Optional[str]  # Add API_KEY

    # Email configurations
    EMAIL_HOST: Optional[str]
    EMAIL_PORT: Optional[int]
    EMAIL_HOST_USER: Optional[str]
    EMAIL_HOST_PASSWORD: Optional[str]
    EMAIL_FROM: Optional[str]

    # Other configurations
    SECRET_KEY: str = 'default_secret_key'
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env")

    # Adding a custom method to validate important fields and throw errors if any are missing
    def validate(self):
        missing_values = []
        if not self.GOOGLE_CLIENT_ID:
            missing_values.append("GOOGLE_CLIENT_ID")
        if not self.GOOGLE_CLIENT_SECRET:
            missing_values.append("GOOGLE_CLIENT_SECRET")
        if not self.MICROSOFT_CLIENT_ID:
            missing_values.append("MICROSOFT_CLIENT_ID")
        if not self.MICROSOFT_CLIENT_SECRET:
            missing_values.append("MICROSOFT_CLIENT_SECRET")
        if not self.EMAIL_HOST:
            missing_values.append("EMAIL_HOST")
        if not self.EMAIL_HOST_USER:
            missing_values.append("EMAIL_HOST_USER")

        if missing_values:
            raise ValueError(f"Missing required configuration values: {', '.join(missing_values)}")

# Initialize settings
settings = Settings()

# Validate the settings
settings.validate()
