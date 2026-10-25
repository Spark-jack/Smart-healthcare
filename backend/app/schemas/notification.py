from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    body: str
    related_patient_id: Optional[int] = None
    related_appointment_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UnreadCountOut(BaseModel):
    unread_count: int

class NotificationPageOut(BaseModel):
    items: List[NotificationOut]
    total: int
    unread_count: int
    page: int
    page_size: int
