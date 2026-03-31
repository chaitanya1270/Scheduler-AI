from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.v1.calendar_demo import service

calendar_demo_router = APIRouter()

@calendar_demo_router.get("/calendar_events", status_code=201)
def fetch_and_store_calendar_events(user_email: str, db: Session = Depends(get_db)):
    try:
        return service.fetch_and_store_calendar_events(user_email, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
