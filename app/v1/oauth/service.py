import requests
import httpx
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session
from app.db import models
from config import settings

def exchange_google_code_for_token(code):
    data = {
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }
    response = requests.post(settings.GOOGLE_TOKEN_URL, data=data)
    response.raise_for_status()
    print('response', response)
    return response.json()

def get_google_user_info(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(settings.GOOGLE_USERINFO_URL, headers=headers)
    response.raise_for_status()
    return response.json()


def upsert_user(db: Session, user_info: dict, token_data: dict, provider: str):
    email = user_info.get('email')
    user_id = user_info.get('id')  # Directly use user_id as a string

    # Check if user exists in the database
    user = db.query(models.User).filter_by(email=email).first()

    if not user:
        user = models.User(
            user_id=user_id,  # Use provided user_id or generate a new unique string
            email=email,
            provider=provider,
            access_token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_expiry=datetime.utcnow() + timedelta(seconds=int(token_data.get('expires_in', 0))),
            oauth_token=str(token_data),  # Convert to string for Text storage
            working_hours_start=time(9, 0),  # Default working hours
            working_hours_end=time(17, 0)    # Default working hours
        )
        db.add(user)
    else:
        # Update existing user tokens
        user.provider = provider
        user.access_token = token_data.get('access_token')
        user.refresh_token = token_data.get('refresh_token')
        user.token_expiry = datetime.utcnow() + timedelta(seconds=int(token_data.get('expires_in', 0)))
        user.oauth_token = str(token_data)  # Convert to string for Text storage

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        raise

    return user

async def refresh_google_token(user: models.User, db: Session):
    data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'refresh_token': user.refresh_token,
        'grant_type': 'refresh_token',
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(settings.GOOGLE_TOKEN_URL, data=data)
        response.raise_for_status()
        token_data = response.json()
    
    user.access_token = token_data['access_token']
    user.token_expiry = datetime.utcnow() + timedelta(seconds=int(token_data['expires_in']))
    db.commit()
    db.refresh(user)
    return token_data