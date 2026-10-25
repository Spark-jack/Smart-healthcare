import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.appointment import Appointment, AppointmentStatus
from app.models.prediction import RiskPrediction
from app.models.notification import Notification, NotificationType, EmailOutbox

class NotificationService:
    @staticmethod
    def send_email(db: Session, to_email: str, subject: str, body: str) -> EmailOutbox:
        """
        Sends an email via SMTP if configured, or logs to console and stores in EmailOutbox with status='logged'.
        Guaranteed not to crash if SMTP fails or is unconfigured.
        """
        outbox = EmailOutbox(
            to_email=to_email,
            subject=subject,
            body=body,
            status="pending",
            attempts=0
        )
        db.add(outbox)
        db.flush()

        smtp_host = settings.SMTP_HOST
        if not smtp_host:
            # SMTP not configured: log to console & set status='logged'
            print(f"[NOTIFICATION EMAIL LOGGED] To: {to_email} | Subject: {subject} | Body: {body[:60]}...")
            outbox.status = "logged"
            outbox.attempts = 1
            outbox.sent_at = datetime.now(timezone.utc)
            db.commit()
            return outbox

        # SMTP configured: attempt delivery
        try:
            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            outbox.status = "sent"
            outbox.attempts = 1
            outbox.sent_at = datetime.now(timezone.utc)
        except Exception as e:
            print(f"[Warning] SMTP delivery failed to {to_email}: {e}")
            outbox.status = "failed"
            outbox.attempts = 1
            outbox.error_message = str(e)

        db.commit()
        return outbox

    @classmethod
    def create_notification(
        cls,
        db: Session,
        user_id: int,
        type: NotificationType,
        title: str,
        body: str,
        related_patient_id: Optional[int] = None,
        related_appointment_id: Optional[int] = None,
        email_subject: Optional[str] = None,
        email_body: Optional[str] = None
    ) -> Notification:
        """
        Creates an in-app Notification record and queues an email via EmailOutbox.
        Never puts clinical details into email subject lines.
        """
        notif = Notification(
            user_id=user_id,
            type=type.value if hasattr(type, "value") else str(type),
            title=title,
            body=body,
            related_patient_id=related_patient_id,
            related_appointment_id=related_appointment_id,
            is_read=False,
            created_at=datetime.now(timezone.utc)
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)

        # Look up recipient email
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.email:
            sub = email_subject or "SmartHealth Portal Notification"
            b = email_body or f"Hello {user.full_name},\n\nYou have a new notification in your SmartHealth portal:\n\n{title}\n\nPlease sign in to your dashboard to review full clinical updates.\n\nSmartHealth.AI System"
            cls.send_email(db, user.email, sub, b)

        return notif

    @classmethod
    def notify_high_risk_flag(cls, db: Session, patient: User, prediction: RiskPrediction):
        """
        Fires HIGH_RISK_FLAG to all active doctors when a prediction produces Critical or High urgency.
        """
        if prediction.urgency_level not in ("Critical", "High"):
            return

        # Extract top drivers for clinician summary
        top_factors = []
        if prediction.cardio_shap_explanation:
            top_factors += [f["feature_label"] for f in prediction.cardio_shap_explanation.get("top_factors", []) if f.get("impact") == "increases_risk"]
        if prediction.diabetes_shap_explanation:
            top_factors += [f["feature_label"] for f in prediction.diabetes_shap_explanation.get("top_factors", []) if f.get("impact") == "increases_risk"]
        
        top_drivers = ", ".join(top_factors[:2]) if top_factors else "Acute clinical telemetry flags"

        doctors = db.query(User).filter(User.role == UserRole.DOCTOR, User.is_active == True).all()
        for doc in doctors:
            title = f"High Urgency Alert: {patient.full_name} ({prediction.urgency_level})"
            body = (
                f"Patient {patient.full_name} has generated an urgent {prediction.urgency_level} risk score of {prediction.overall_risk_score}%. "
                f"Primary drivers: {top_drivers}. Access deep-dive file for clinical evaluation."
            )
            cls.create_notification(
                db=db,
                user_id=doc.id,
                type=NotificationType.HIGH_RISK_FLAG,
                title=title,
                body=body,
                related_patient_id=patient.id,
                email_subject="SmartHealth: Priority Clinical Patient Alert",
                email_body=(
                    f"Dr. {doc.full_name},\n\n"
                    f"A monitored patient has generated a high-urgency clinical indicator requiring physician review.\n"
                    f"Please log in to your clinical triage portal to review their deep-dive profile and medical telemetry.\n\n"
                    f"SmartHealth.AI Clinical System"
                )
            )

    @classmethod
    def notify_appointment_booked(cls, db: Session, appointment: Appointment):
        """
        Notifies patient and doctor that an appointment has been booked.
        """
        patient = db.query(User).filter(User.id == appointment.patient_id).first()
        doctor = db.query(User).filter(User.id == appointment.doctor_id).first() if appointment.doctor_id else None
        doc_name = doctor.full_name if doctor else "Attending Physician"
        pat_name = patient.full_name if patient else f"Patient #{appointment.patient_id}"

        # 1. Notify Patient
        cls.create_notification(
            db=db,
            user_id=appointment.patient_id,
            type=NotificationType.APPOINTMENT_BOOKED,
            title="Consultation Confirmed",
            body=f"Your consultation with {doc_name} is scheduled for {appointment.appointment_date} at {appointment.appointment_time} (Triage: {appointment.urgency_level.value}).",
            related_appointment_id=appointment.id,
            related_patient_id=appointment.patient_id,
            email_subject="SmartHealth: Appointment Scheduled",
            email_body=(
                f"Dear {pat_name},\n\n"
                f"Your consultation has been scheduled for {appointment.appointment_date} at {appointment.appointment_time}.\n"
                f"Please log in to your patient portal for location, preparation notes, and status updates.\n\n"
                f"SmartHealth Care Team"
            )
        )

        # 2. Notify Doctor (or all doctors if unassigned)
        if doctor:
            target_docs = [doctor]
        else:
            target_docs = db.query(User).filter(User.role == UserRole.DOCTOR, User.is_active == True).all()

        for d in target_docs:
            cls.create_notification(
                db=db,
                user_id=d.id,
                type=NotificationType.APPOINTMENT_BOOKED,
                title="New Patient Consultation Scheduled",
                body=f"Patient {pat_name} booked a consultation for {appointment.appointment_date} at {appointment.appointment_time} (Triage: {appointment.urgency_level.value}).",
                related_appointment_id=appointment.id,
                related_patient_id=appointment.patient_id,
                email_subject="SmartHealth: New Appointment Scheduled",
                email_body=(
                    f"Dr. {d.full_name},\n\n"
                    f"A new consultation has been booked on your calendar for {appointment.appointment_date} at {appointment.appointment_time}.\n"
                    f"Please log in to your clinical schedule to review details.\n\n"
                    f"SmartHealth.AI System"
                )
            )

    @classmethod
    def notify_appointment_status_changed(cls, db: Session, appointment: Appointment, old_status: str, new_status: str):
        """
        Notifies patient when appointment status changes (e.g. confirmed, completed, cancelled).
        """
        patient = db.query(User).filter(User.id == appointment.patient_id).first()
        doctor = db.query(User).filter(User.id == appointment.doctor_id).first() if appointment.doctor_id else None
        doc_name = doctor.full_name if doctor else "Your Physician"
        pat_name = patient.full_name if patient else "Patient"

        cls.create_notification(
            db=db,
            user_id=appointment.patient_id,
            type=NotificationType.APPOINTMENT_STATUS_CHANGED,
            title=f"Appointment {new_status.capitalize()}",
            body=f"Your consultation on {appointment.appointment_date} has been updated to '{new_status}' by {doc_name}.",
            related_appointment_id=appointment.id,
            related_patient_id=appointment.patient_id,
            email_subject="SmartHealth: Appointment Status Update",
            email_body=(
                f"Dear {pat_name},\n\n"
                f"The status of your appointment scheduled for {appointment.appointment_date} has changed to: {new_status}.\n"
                f"Please log in to your patient portal to review clinical notes or reschedule if necessary.\n\n"
                f"SmartHealth Portal"
            )
        )

    @classmethod
    def notify_risk_updated(cls, db: Session, patient: User, old_category: str, new_category: str, prediction: RiskPrediction):
        """
        Notifies patient when a new survey produces a materially different risk category.
        """
        if old_category == new_category:
            return

        cls.create_notification(
            db=db,
            user_id=patient.id,
            type=NotificationType.RISK_UPDATED,
            title="Health Risk Profile Updated",
            body=f"Your calculated health risk category changed from {old_category} to {new_category} (Overall Risk: {prediction.overall_risk_score}%). Check your dashboard for personalized insights.",
            related_patient_id=patient.id,
            email_subject="SmartHealth: Health Profile Update",
            email_body=(
                f"Dear {patient.full_name},\n\n"
                f"A new predictive health analysis was calculated for your account.\n"
                f"Please log in to your patient portal to review your updated health summary and lifestyle recommendations.\n\n"
                f"SmartHealth.AI Preventive Care"
            )
        )

    @classmethod
    def send_appointment_reminders(cls, db: Session) -> int:
        """
        Idempotent 24-hour appointment reminder job.
        Finds appointments scheduled roughly 24 hours from now (within tomorrow's window),
        and sends APPOINTMENT_REMINDER if not already sent.
        """
        now = datetime.now(timezone.utc)
        target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Query pending/confirmed appointments scheduled on target_date
        appts = db.query(Appointment).filter(
            Appointment.appointment_date == target_date,
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        ).all()

        reminders_sent = 0
        for appt in appts:
            # Idempotency check: verify a reminder has not already been sent for this appointment
            existing = db.query(Notification).filter(
                Notification.user_id == appt.patient_id,
                Notification.type == NotificationType.APPOINTMENT_REMINDER.value,
                Notification.related_appointment_id == appt.id
            ).first()

            if existing is not None:
                continue

            patient = db.query(User).filter(User.id == appt.patient_id).first()
            doctor = db.query(User).filter(User.id == appt.doctor_id).first() if appt.doctor_id else None
            doc_name = doctor.full_name if doctor else "Your Attending Physician"
            pat_name = patient.full_name if patient else "Patient"

            cls.create_notification(
                db=db,
                user_id=appt.patient_id,
                type=NotificationType.APPOINTMENT_REMINDER,
                title="Consultation Reminder (24 Hours)",
                body=f"Reminder: You have a consultation tomorrow, {appt.appointment_date} at {appt.appointment_time} with {doc_name}.",
                related_appointment_id=appt.id,
                related_patient_id=appt.patient_id,
                email_subject="SmartHealth: Upcoming Consultation Reminder",
                email_body=(
                    f"Dear {pat_name},\n\n"
                    f"This is a reminder for your upcoming consultation scheduled on {appt.appointment_date} at {appt.appointment_time}.\n"
                    f"Please log in to your patient portal if you need to review consultation notes.\n\n"
                    f"SmartHealth Care Team"
                )
            )
            reminders_sent += 1

        return reminders_sent

notification_service = NotificationService()
