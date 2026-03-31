from datetime import datetime, time
from sqlalchemy import (
    Column, String, DateTime, Text, Time, ForeignKey, Integer, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import pytz
from enum import Enum as PyEnum
from sqlalchemy import Enum


Base = declarative_base()


def to_utc(dt):
    """Converts a naive datetime or ISO 8601 string to UTC."""
    if isinstance(dt, str):
        # Use fromisoformat for ISO 8601 format (it handles 'Z' for UTC)
        if dt.endswith('Z'):
            dt = dt[:-1] + '+00:00'  # Convert 'Z' to '+00:00'
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)  # Assume naive times are UTC
    return dt.astimezone(pytz.utc)


# User Model
class User(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)  # 'google' or 'microsoft'
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)  # Expiry in UTC
    oauth_token = Column(Text, nullable=True)  # Store access_token, refresh_token, etc.
    working_hours_start = Column(Time, default=time(9, 0), nullable=True)  # Start of working hours
    working_hours_end = Column(Time, default=time(17, 0), nullable=True)    # End of working hours

    # Relationships
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    availabilities = relationship("Availability", back_populates="user", cascade="all, delete-orphan")
    meetings = relationship('Meeting', back_populates='organizer', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, email={self.email}, provider={self.provider})>"


# Utility function to convert string or naive datetime to UTC


# Update __init__ method in CalendarEvent, Availability, Meeting, etc.

class CalendarEvent(Base):
    __tablename__ = 'calendar_events'

    id = Column(String, primary_key=True, unique=True, nullable=False)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    start_time = Column(DateTime, nullable=False)  # Event start time in UTC
    end_time = Column(DateTime, nullable=False)    # Event end time in UTC
    title = Column(String, nullable=False)         # Title of the event
    description = Column(Text, nullable=True)      # Event description
    location = Column(String, nullable=True)       # Event location

    user = relationship("User", back_populates="calendar_events")

    def __init__(self, **kwargs):
        if 'start_time' in kwargs:
            kwargs['start_time'] = to_utc(kwargs['start_time'])
        if 'end_time' in kwargs:
            kwargs['end_time'] = to_utc(kwargs['end_time'])
        super(CalendarEvent, self).__init__(**kwargs)

    def __repr__(self):
        return f"<CalendarEvent(id={self.id}, user_id={self.user_id}, title={self.title})>"




# Availability Model
class Availability(Base):
    __tablename__ = 'availabilities'

    id = Column(String, primary_key=True, unique=True, nullable=False)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    start_time = Column(DateTime, nullable=False)  # Availability start time in UTC
    end_time = Column(DateTime, nullable=False)    # Availability end time in UTC
    status = Column(String, nullable=False)        # e.g., 'free', 'busy'

    # Relationship to User
    user = relationship("User", back_populates="availabilities")

    def __init__(self, **kwargs):
        if 'start_time' in kwargs:
            kwargs['start_time'] = to_utc(kwargs['start_time'])
        if 'end_time' in kwargs:
            kwargs['end_time'] = to_utc(kwargs['end_time'])
        super(Availability, self).__init__(**kwargs)

    def __repr__(self):
        return f"<Availability(id={self.id}, user_id={self.user_id}, status={self.status})>"


# Meeting Model

class Meeting(Base):
    __tablename__ = 'meetings'
    meeting_id = Column(String, primary_key=True, unique=True, nullable=False)
    organizer_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default='scheduled')  # e.g., 'scheduled', 'cancelled'
    start_time = Column(DateTime, nullable=False)  # Meeting start time in UTC
    end_time = Column(DateTime, nullable=False)    # Meeting end time in UTC
    start_time_window = Column(DateTime, nullable=True)  # Optional start time window
    end_time_window = Column(DateTime, nullable=True)    # Optional end time window
    priority = Column(String, nullable=False)      # 'critical', 'high', 'medium', 'low'
    risk_score = Column(Float, nullable=False)
    feasibility_score = Column(Float, nullable=False)
    calendar_event_id = Column(String, nullable=True)

    organizer = relationship('User', back_populates='meetings')
    participants = relationship('MeetingParticipant', back_populates='meeting', cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        # Ensure the times are stored in UTC
        if 'start_time' in kwargs:
            kwargs['start_time'] = to_utc(kwargs['start_time'])
        if 'end_time' in kwargs:
            kwargs['end_time'] = to_utc(kwargs['end_time'])
        if 'start_time_window' in kwargs:
            kwargs['start_time_window'] = to_utc(kwargs['start_time_window'])
        if 'end_time_window' in kwargs:
            kwargs['end_time_window'] = to_utc(kwargs['end_time_window'])
        super(Meeting, self).__init__(**kwargs)

    def __repr__(self):
        return f"<Meeting(meeting_id={self.meeting_id}, organizer_id={self.organizer_id}, title={self.title})>"



# MeetingParticipant Model
class MeetingParticipant(Base):
    __tablename__ = 'meeting_participants'

    id = Column(String, primary_key=True, unique=True, nullable=False)
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=True)
    email = Column(String, nullable=False)
    role = Column(String, default='participant')  # e.g., 'participant', 'optional'
    accepted = Column(Integer, default=0)         # 0: Pending, 1: Accepted, -1: Declined
    last_notified = Column(DateTime, nullable=True)  # Last notification time in UTC

    meeting = relationship('Meeting', back_populates='participants')
    user = relationship('User')

    def __init__(self, **kwargs):
        if 'last_notified' in kwargs:
            kwargs['last_notified'] = to_utc(kwargs['last_notified'])
        super(MeetingParticipant, self).__init__(**kwargs)

    def __repr__(self):
        return f"<MeetingParticipant(id={self.id}, meeting_id={self.meeting_id}, email={self.email})>"


# DeclinedMeeting Model
class DeclinedMeeting(Base):
    __tablename__ = 'declined_meetings'

    id = Column(String, primary_key=True, unique=True, nullable=False)
    meeting_id = Column(String, ForeignKey('meetings.meeting_id'), nullable=False)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=True)
    email = Column(String, nullable=False)
    declined_at = Column(DateTime, default=datetime.utcnow)  # Default to UTC
    reason = Column(Text, nullable=True)

    meeting = relationship('Meeting')
    user = relationship('User')

    def __init__(self, **kwargs):
        if 'declined_at' in kwargs:
            kwargs['declined_at'] = to_utc(kwargs['declined_at'])
        super(DeclinedMeeting, self).__init__(**kwargs)

    def __repr__(self):
        return f"<DeclinedMeeting(id={self.id}, meeting_id={self.meeting_id}, email={self.email})>"
