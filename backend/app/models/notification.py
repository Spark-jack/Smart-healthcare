from datetime import datetime, timezone
import enum
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base

class NotificationType(str, enum.Enum):
    HIGH_RISK_FLAG = "HIGH_RISK_FLAG"
    APPOINTMENT_BOOKED = "APPOINTMENT_BOOKED"
    APPOINTMENT_STATUS_CHANGED = "APPOINTMENT_STATUS_CHANGED"
    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"
    RISK_UPDATED = "RISK_UPDATED"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    related_patient_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    related_appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id])
    related_patient = relationship("User", foreign_keys=[related_patient_id])
    related_appointment = relationship("Appointment", foreign_keys=[related_appointment_id])

class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, sent, logged, failed
    attempts = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
