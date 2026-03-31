from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from urllib.parse import urlencode
from app.db.database import get_db
from app.v1.oauth import service as oauth_service
from config import settings

oauth_router = APIRouter()

# Route to initiate Google OAuth flow
@oauth_router.get('/google')
async def initiate_google_oauth():
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile https://www.googleapis.com/auth/calendar',
        'access_type': 'offline',
        'prompt': 'consent',
    }
    url = f"{settings.GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)

# Route to handle Google OAuth callback
@oauth_router.get('/google/redirect')
async def handle_google_oauth_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get('code')
    print(code)
    if not code:
        raise HTTPException(status_code=400, detail="Missing code in callback")

    try:
        # Exchange code for tokens
        token_data = oauth_service.exchange_google_code_for_token(code)
        print("Token data received:", token_data)

        # Get user info
        user_info = oauth_service.get_google_user_info(token_data['access_token'])
        print("User info received:", user_info)

        # Store or update user in the database
        user = oauth_service.upsert_user(db, user_info, token_data, provider='google')

        if user:
            print(f"User {user.email} stored in database with ID: {user.user_id}")
            return RedirectResponse(url="http://localhost:3001/calendar")
        else:
            print("Failed to insert/update user in the database.")
            raise HTTPException(status_code=500, detail="Failed to store user data")
        
    except Exception as e:
        print(f"An error occurred during the OAuth process: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
