# app/v1/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.models import User
from app.supabase_auth import verify_user
from app.db.database import get_db
from app.v1.models import MeetingSlotRequest
from core.scheduler import fetch_and_filter_availability, find_best_meeting_times
from core.suggest_alternative import suggest_alternatives
from app.v1.calendar.service import store_event_data
from datetime import datetime, timedelta

calendar_router = APIRouter()



@calendar_router.post("/events/store")
async def store_user_events(token: str, event_data: dict, db: Session = Depends(get_db)):
    user_data = await verify_user(token)
    if not user_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = user_data['id']

    # Store event data using the service function
    try:
        stored_event = store_event_data(db, event_data, user_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return {"message": "Event stored successfully", "event": stored_event}

