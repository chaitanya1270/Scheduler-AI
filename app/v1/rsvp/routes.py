from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import models

rsvp_router = APIRouter()

@rsvp_router.post("/rsvp/respond")
def respond_to_invite(
    meeting_id: str,
    user_email: str,
    response: str,  # 'accept' or 'decline'
    db: Session = Depends(get_db)
):
    participant = db.query(models.MeetingParticipant).filter(
        models.MeetingParticipant.meeting_id == meeting_id,
        models.MeetingParticipant.email == user_email
    ).first()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    if response.lower() == 'accept':
        participant.accepted = 1
    elif response.lower() == 'decline':
        participant.accepted = -1
        declined_meeting = models.DeclinedMeeting(
            meeting_id=meeting_id,
            user_id=participant.user_id,
            email=participant.email,
            reason="User declined the invite."  # Optionally, capture from request
        )
        db.add(declined_meeting)
    else:
        raise HTTPException(status_code=400, detail="Invalid response")

    db.commit()
    db.refresh(participant)

    return {"message": "RSVP updated successfully"}
