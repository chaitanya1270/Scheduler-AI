from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.v1.alternative_suggestions.service import suggest_alternative_slots
from pydantic import BaseModel

# Define a model to accept the request body
class MeetingRejectionRequest(BaseModel):
    meeting_id: str  # Adjust the type if your meeting_id is a string

alternative_suggestions_router = APIRouter()

@alternative_suggestions_router.post("/handle_rejection")
async def handle_rejected_meeting_slot(request: MeetingRejectionRequest, db: Session = Depends(get_db)):
    """
    API endpoint to handle a rejected meeting and suggest alternative slots.
    """
    try:
        result=await suggest_alternative_slots(db, request.meetinng_id)
        print(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
