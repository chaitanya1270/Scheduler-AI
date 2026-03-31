from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db  # Assuming you have a dependency to get the DB session
from app.v1.schedule_demo.service import schedule_meeting
from app.v1.models import MeetingSlotRequest

schedule_demo_router = APIRouter()

# Changing the method to POST and using a request body for the parameters
@schedule_demo_router.post("/schedule-meeting")
async def schedule_meeting_route(
    request: MeetingSlotRequest,  # Accepting the request body directly as JSON
    db: Session = Depends(get_db)  # Using dependency injection for the DB session
):
    # Call the scheduling service and pass the database session
    return await schedule_meeting(request=request, db=db)
