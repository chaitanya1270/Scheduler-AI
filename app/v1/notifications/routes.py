from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.v1.notifications import service as notif_service
from app.v1.communication import service as comm_service

notifications_router = APIRouter()

@notifications_router.post("/notifications/send_manual")
def send_manual_notifications(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    participants = db.query(models.MeetingParticipant).filter(
        models.MeetingParticipant.meeting_id == meeting_id,
        models.MeetingParticipant.accepted == 0
    ).all()
    
    for participant in participants:
        comm_service.notify_participant(
            background_tasks=BackgroundTasks(),
            participant=participant,
            meeting_title=meeting.title,
            slot_start=meeting.start_time.strftime("%Y-%m-%d %H:%M"),
            slot_end=meeting.end_time.strftime("%Y-%m-%d %H:%M"),
            message="Please respond to this meeting invitation."
        )
    
    return {"message": "Manual notifications sent to pending participants."}
