from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.appointment import UrgencyLevel, AppointmentStatus

class AppointmentCreate(BaseModel):
    doctor_id: Optional[int] = None
    appointment_date: str # YYYY-MM-DD
    appointment_time: str # e.g. "09:30 AM"
    reason: str
    symptoms_summary: Optional[str] = None

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    doctor_notes: Optional[str] = None

class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    appointment_date: str
    appointment_time: str
    reason: str
    symptoms_summary: Optional[str] = None
    urgency_score: float
    urgency_level: UrgencyLevel
    status: AppointmentStatus
    doctor_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UrgencyCalculationResult(BaseModel):
    urgency_score: float
    urgency_level: str
    breakdown: dict
    recommended_timeframe: str
