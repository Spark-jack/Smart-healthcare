import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class UrgencyLevel(str, enum.Enum):
    ROUTINE = "Routine"       # 0 - 39
    MODERATE = "Moderate"     # 40 - 64
    HIGH = "High"             # 65 - 84
    CRITICAL = "Critical"     # 85 - 100

class AppointmentStatus(str, enum.Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    appointment_date = Column(String(50), nullable=False) # e.g. YYYY-MM-DD
    appointment_time = Column(String(50), nullable=False) # e.g. 10:00 AM
    reason = Column(String(255), nullable=False)
    symptoms_summary = Column(Text, nullable=True)

    urgency_score = Column(Float, nullable=False, default=20.0)
    urgency_level = Column(Enum(UrgencyLevel), default=UrgencyLevel.ROUTINE, nullable=False)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False)
    doctor_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_appointments")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_appointments")
