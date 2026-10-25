from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_doctor
from app.models.user import User, UserRole
from app.models.appointment import Appointment, UrgencyLevel, AppointmentStatus
from app.models.prediction import RiskPrediction
from app.schemas.triage import AppointmentCreate, AppointmentOut, AppointmentStatusUpdate
from app.services.notification_service import notification_service

router = APIRouter(prefix="/triage", tags=["Urgency Triage & Appointments"])

def _format_appointment(app: Appointment) -> AppointmentOut:
    patient_name = app.patient.full_name if app.patient else f"Patient #{app.patient_id}"
    doctor_name = app.doctor.full_name if app.doctor else "Any Available Attending Physician"
    return AppointmentOut(
        id=app.id,
        patient_id=app.patient_id,
        patient_name=patient_name,
        doctor_id=app.doctor_id,
        doctor_name=doctor_name,
        appointment_date=app.appointment_date,
        appointment_time=app.appointment_time,
        reason=app.reason,
        symptoms_summary=app.symptoms_summary,
        urgency_score=app.urgency_score,
        urgency_level=app.urgency_level,
        status=app.status,
        doctor_notes=app.doctor_notes,
        created_at=app.created_at
    )

@router.post("/appointments", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def book_appointment(
    appt_in: AppointmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Fetch patient's latest risk prediction to assign urgency
    latest_pred = db.query(RiskPrediction).filter(
        RiskPrediction.user_id == current_user.id
    ).order_by(RiskPrediction.created_at.desc()).first()

    if latest_pred:
        urgency_score = latest_pred.urgency_score
        urgency_level_str = latest_pred.urgency_level
        urgency_level = getattr(UrgencyLevel, urgency_level_str.upper(), UrgencyLevel.ROUTINE)
    else:
        urgency_score = 25.0
        urgency_level = UrgencyLevel.ROUTINE

    appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=appt_in.doctor_id,
        appointment_date=appt_in.appointment_date,
        appointment_time=appt_in.appointment_time,
        reason=appt_in.reason,
        symptoms_summary=appt_in.symptoms_summary,
        urgency_score=urgency_score,
        urgency_level=urgency_level,
        status=AppointmentStatus.PENDING
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    # Dispatch APPOINTMENT_BOOKED notification
    notification_service.notify_appointment_booked(db, appointment)

    return _format_appointment(appointment)

@router.get("/appointments", response_model=List[AppointmentOut])
def list_appointments(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role == UserRole.PATIENT:
        appts = db.query(Appointment).filter(
            Appointment.patient_id == current_user.id
        ).order_by(Appointment.created_at.desc()).all()
    elif current_user.role == UserRole.DOCTOR:
        appts = db.query(Appointment).filter(
            (Appointment.doctor_id == current_user.id) | (Appointment.doctor_id == None)
        ).order_by(Appointment.urgency_score.desc(), Appointment.created_at.asc()).all()
    else: # Admin
        appts = db.query(Appointment).order_by(Appointment.urgency_score.desc()).all()

    return [_format_appointment(a) for a in appts]

@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentOut)
def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    old_status = appt.status.value if hasattr(appt.status, "value") else str(appt.status)
    appt.status = status_update.status
    if status_update.doctor_notes is not None:
        appt.doctor_notes = status_update.doctor_notes

    db.commit()
    db.refresh(appt)

    # Dispatch APPOINTMENT_STATUS_CHANGED notification
    new_status = appt.status.value if hasattr(appt.status, "value") else str(appt.status)
    if old_status != new_status:
        notification_service.notify_appointment_status_changed(db, appt, old_status, new_status)

    return _format_appointment(appt)
