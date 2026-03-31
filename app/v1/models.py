from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class MeetingSlotRequest(BaseModel):
    participants: list[str]
    meeting_duration: int  # Duration in minutes
    meeting_title: str
    meeting_description: str
    start_time_window: datetime
    end_time_window: datetime
    priority: str  # 'critical', 'high', 'medium', 'low'

class ScheduleMeetingRequest(BaseModel):
    participants: list[str]
    meeting_title: str
    meeting_description: str
    slot_start: datetime
    slot_end: datetime
    start_time_window: datetime
    end_time_window: datetime
    priority: str  # 'critical', 'high', 'medium', 'low'

class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
