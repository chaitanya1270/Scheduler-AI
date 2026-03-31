from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db import models
from app.v1.communication import service as comm_service

communication_router = APIRouter()

@communication_router.post("/send_notifications")
def send_notifications_route(
    meeting_id: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Fetch meeting using the meeting_id as a string
    meeting = db.query(models.Meeting).filter(models.Meeting.meeting_id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Retrieve participants with a pending status
    participants = db.query(models.MeetingParticipant).filter(
        models.MeetingParticipant.meeting_id == meeting_id,
        models.MeetingParticipant.accepted == 0  # Pending
    ).all()
    
    # Generate .ics file for the meeting
    ics_file = comm_service.generate_ics_file(
        meeting_title=meeting.title,
        slot_start=meeting.start_time,
        slot_end=meeting.end_time,
        description=meeting.description or "",
        location=""
    )
    
    # Notify each participant
    for participant in participants:
        comm_service.notify_participant(
            background_tasks,
            participant.email,
            meeting.title,
            meeting.start_time.strftime("%Y-%m-%d %H:%M"),
            meeting.end_time.strftime("%Y-%m-%d %H:%M"),
            "You have been invited to a meeting. Please respond to this invitation.",
            ics_file=ics_file,
            ics_filename=f"{meeting.title}.ics"
        )
    
    return {"message": "Notifications sent to pending participants."}
