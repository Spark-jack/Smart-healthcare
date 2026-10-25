import pytest
from datetime import datetime, date, time, timedelta
from app.models.user import UserRole
from app.models.notification import Notification, NotificationType
from app.models.appointment import Appointment, UrgencyLevel, AppointmentStatus
from app.services.notification_service import notification_service

def test_survey_creates_prediction_and_high_risk_notification(client, db_session, create_user):
    # Setup a doctor and a patient
    doctor = create_user("doc_triage@test.com", "DocPass123!", "Dr. Cardiologist", UserRole.DOCTOR)
    patient = create_user("patient_crit@test.com", "PatientPass123!", "Crit Patient", UserRole.PATIENT)

    token = client.post("/api/v1/auth/token", data={
        "username": "patient_crit@test.com",
        "password": "PatientPass123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Submit a critical survey: Hypertensive crisis (BP 190/125), chest pain type 0, high ST depression
    survey_payload = {
        "age": 60,
        "gender": "Male",
        "height_cm": 175.0,
        "weight_kg": 95.0,
        "systolic_bp": 190,
        "diastolic_bp": 125,
        "total_cholesterol": 280,
        "fasting_blood_sugar": 260.0,
        "resting_ecg": 2,
        "max_heart_rate": 165,
        "smoker": True,
        "physical_activity": False,
        "fruits_diet": False,
        "veggies_diet": False,
        "heavy_alcohol": False,
        "chest_pain_type": 0,
        "exercise_angina": True,
        "st_depression": 2.8,
        "st_slope": 2,
        "major_vessels": 2,
        "general_health": 5,
        "physical_health_days": 15,
        "mental_health_days": 10,
        "diff_walking": True,
        "stroke_history": True,
        "heart_disease_history": True
    }

    res = client.post("/api/v1/surveys/", json=survey_payload, headers=headers)
    assert res.status_code == 201, res.text
    pred_data = res.json()
    assert pred_data["urgency_level"] in ["Critical", "High"]

    # Check notification sent to doctor
    notifications = db_session.query(Notification).filter(
        Notification.user_id == doctor.id,
        Notification.type == NotificationType.HIGH_RISK_FLAG
    ).all()
    assert len(notifications) >= 1
    high_risk_note = notifications[0]
    assert "Crit Patient" in high_risk_note.title or "Crit Patient" in high_risk_note.body
    assert high_risk_note.is_read is False

def test_appointment_booking_stores_urgency_and_notifies(client, db_session, create_user):
    doctor = create_user("doc_appt@test.com", "DocPass123!", "Dr. Appt", UserRole.DOCTOR)
    patient = create_user("patient_appt@test.com", "PatientPass123!", "Appt Patient", UserRole.PATIENT)

    token = client.post("/api/v1/auth/token", data={
        "username": "patient_appt@test.com",
        "password": "PatientPass123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    appt_payload = {
        "doctor_id": doctor.id,
        "appointment_date": "2026-11-05",
        "appointment_time": "10:30",
        "reason": "Cardiology Consultation",
        "symptoms_summary": "Exertional dyspnea and hypertension"
    }

    res = client.post("/api/v1/triage/appointments", json=appt_payload, headers=headers)
    assert res.status_code == 201, res.text
    appt_data = res.json()
    assert appt_data["doctor_id"] == doctor.id
    assert appt_data["urgency_level"] is not None
    assert appt_data["urgency_score"] is not None

    # Check notification sent to doctor
    doc_notifications = db_session.query(Notification).filter(
        Notification.user_id == doctor.id,
        Notification.type == NotificationType.APPOINTMENT_BOOKED
    ).all()
    assert len(doc_notifications) >= 1

def test_notification_endpoints(client, db_session, create_user):
    patient = create_user("patient_notes@test.com", "PatientPass123!", "Notes Patient", UserRole.PATIENT)
    token = client.post("/api/v1/auth/token", data={
        "username": "patient_notes@test.com",
        "password": "PatientPass123!"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Seed 2 notifications for this patient
    n1 = Notification(
        user_id=patient.id,
        type=NotificationType.APPOINTMENT_BOOKED,
        title="Appointment Confirmed",
        body="Your appointment has been booked.",
        is_read=False
    )
    n2 = Notification(
        user_id=patient.id,
        type=NotificationType.RISK_UPDATED,
        title="Health Risk Updated",
        body="Your recent survey updated your risk profile.",
        is_read=False
    )
    db_session.add_all([n1, n2])
    db_session.commit()

    # 1. Unread count
    count_res = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] == 2

    # 2. Get list
    list_res = client.get("/api/v1/notifications", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) == 2

    # 3. Mark single as read
    patch_res = client.patch(f"/api/v1/notifications/{n1.id}/read", headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["is_read"] is True

    # 4. Check unread count is now 1
    count_res2 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res2.json()["unread_count"] == 1

    # 5. Mark all as read
    read_all_res = client.post("/api/v1/notifications/read-all", headers=headers)
    assert read_all_res.status_code == 200

    # 6. Check unread count is 0
    count_res3 = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_res3.json()["unread_count"] == 0

def test_reminder_job_idempotency(db_session, create_user):
    doctor = create_user("doc_remind@test.com", "DocPass123!", "Dr. Remind", UserRole.DOCTOR)
    patient = create_user("patient_remind@test.com", "PatientPass123!", "Remind Patient", UserRole.PATIENT)

    # Create an appointment ~24 hours from today
    tomorrow = date.today() + timedelta(days=1)
    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        appointment_date=tomorrow.isoformat(),
        appointment_time="14:00",
        reason="Followup check",
        status=AppointmentStatus.CONFIRMED,
        urgency_score=30.0,
        urgency_level=UrgencyLevel.ROUTINE
    )
    db_session.add(appt)
    db_session.commit()
    db_session.refresh(appt)

    # First run of reminder job
    sent_count_1 = notification_service.send_appointment_reminders(db_session)
    assert sent_count_1 == 1, "First run should create 1 reminder for the 24h appointment"

    # Verify notification created
    reminders_1 = db_session.query(Notification).filter(
        Notification.user_id == patient.id,
        Notification.type == NotificationType.APPOINTMENT_REMINDER,
        Notification.related_appointment_id == appt.id
    ).all()
    assert len(reminders_1) == 1

    # Second run of reminder job
    sent_count_2 = notification_service.send_appointment_reminders(db_session)
    assert sent_count_2 == 0, "Second run must be idempotent and not send duplicate reminders"

    # Verify still exactly 1 reminder exists
    reminders_2 = db_session.query(Notification).filter(
        Notification.user_id == patient.id,
        Notification.type == NotificationType.APPOINTMENT_REMINDER,
        Notification.related_appointment_id == appt.id
    ).all()
    assert len(reminders_2) == 1
