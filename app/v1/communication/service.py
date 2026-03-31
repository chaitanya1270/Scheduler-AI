from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List
import asyncio

from app.db import models
from app.db.database import SessionLocal
from app.v1.communication import service as comm_service
from config import settings

scheduler = AsyncIOScheduler()

def determine_notification_frequency(priority: str, risk_score: float, feasibility_score: float) -> timedelta:
    """
    Determine the frequency of notifications based on priority, risk_score, and feasibility_score.
    Higher priority and higher risk scores result in more frequent notifications.
    """
    if priority == 'critical':
        return timedelta(hours=1)
    elif priority == 'high':
        return timedelta(hours=3)
    elif priority == 'medium':
        return timedelta(hours=6)
    else:  # low
        return timedelta(hours=12)

def should_send_notification(meeting: models.Meeting, participant: models.MeetingParticipant) -> bool:
    """Determine if a notification should be sent based on the last notified time."""
    frequency = determine_notification_frequency(meeting.priority, meeting.risk_score, meeting.feasibility_score)
    if participant.last_notified:
        next_notification_time = participant.last_notified + frequency
    else:
        # Start notifications immediately if not previously notified
        next_notification_time = datetime.utcnow()
    
    return datetime.utcnow() >= next_notification_time

def send_periodic_notifications():
    """Periodic task to send notifications to participants who haven't responded."""
    db: Session = SessionLocal()
    try:
        pending_participants = db.query(models.MeetingParticipant).filter(
            models.MeetingParticipant.accepted == 0
        ).all()
        
        for participant in pending_participants:
            meeting = db.query(models.Meeting).filter(models.Meeting.id == participant.meeting_id).first()
            if not meeting:
                continue
            
            if should_send_notification(meeting, participant):
                # Generate .ics file
                ics_file = comm_service.generate_ics_file(
                    meeting_title=meeting.title,
                    slot_start=meeting.start_time,
                    slot_end=meeting.end_time,
                    description=meeting.description or "",
                    location=""
                )
                
                # Send notification
                comm_service.notify_participant(
                    background_tasks=BackgroundTasks(),
                    participant_email=participant.email,
                    meeting_title=meeting.title,
                    slot_start=meeting.start_time.strftime("%Y-%m-%d %H:%M"),
                    slot_end=meeting.end_time.strftime("%Y-%m-%d %H:%M"),
                    message="You have been invited to a meeting. Please respond to this invitation.",
                    ics_file=ics_file,
                    ics_filename=f"{meeting.title}.ics"
                )
                
                # Update last_notified time
                participant.last_notified = datetime.utcnow()
                db.commit()
                
    except Exception as e:
        # Log the exception
        print(f"Error in send_periodic_notifications: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the APScheduler."""
    scheduler.add_job(send_periodic_notifications, 'interval', minutes=30)  # Check every 30 minutes
    scheduler.start()
