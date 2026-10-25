import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.survey import HealthSurvey
from app.models.prediction import RiskPrediction
from app.models.appointment import Appointment, UrgencyLevel, AppointmentStatus
from app.services.ml_engine import ml_engine
from app.services.shap_explainer import shap_service
from app.services.triage_engine import triage_engine

def seed_database():
    print("--------------------------------------------------")
    print("Initializing Database Tables and Seeding Clinical Data...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data for a clean, deterministic seed
    try:
        db.query(Appointment).delete()
        db.query(RiskPrediction).delete()
        db.query(HealthSurvey).delete()
        db.query(User).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print("Note on cleaning tables:", e)

    default_password = get_password_hash("password123")

    # 1. Doctors
    dr_eleanor = User(
        email="dr.eleanor@hospital.org",
        hashed_password=default_password,
        full_name="Dr. Eleanor Vance, MD",
        role=UserRole.DOCTOR,
        specialization="Chief Cardiologist & Interventional Cardiology",
        phone_number="+1 (555) 234-5678"
    )
    dr_marcus = User(
        email="dr.marcus@hospital.org",
        hashed_password=default_password,
        full_name="Dr. Marcus Brody, MD",
        role=UserRole.DOCTOR,
        specialization="Senior Endocrinologist & Diabetologist",
        phone_number="+1 (555) 345-6789"
    )
    dr_sophia = User(
        email="dr.sophia@hospital.org",
        hashed_password=default_password,
        full_name="Dr. Sophia Chen, MD",
        role=UserRole.DOCTOR,
        specialization="Preventive Medicine & Clinical Lipidology",
        phone_number="+1 (555) 456-7890"
    )

    # 2. Admin
    admin_user = User(
        email="admin@hospital.org",
        hashed_password=get_password_hash("admin123"),
        full_name="System Administrator",
        role=UserRole.ADMIN,
        specialization="Health Informatics & IT Operations",
        phone_number="+1 (555) 999-0000"
    )

    # 3. Patient Cohort (Varying Risk Spectrums)
    patients_data = [
        {
            "user": User(
                email="arthur.pendelton@patient.com",
                hashed_password=default_password,
                full_name="Arthur Pendelton",
                role=UserRole.PATIENT,
                phone_number="+1 (555) 101-2001"
            ),
            "survey": {
                "age": 68,
                "gender": "Male",
                "height_cm": 175.0,
                "weight_kg": 96.0,
                "bmi": 31.3,
                "systolic_bp": 178,
                "diastolic_bp": 105,
                "total_cholesterol": 278,
                "fasting_blood_sugar": 185.0,
                "resting_ecg": 2, # LVH
                "max_heart_rate": 112,
                "smoker": True,
                "physical_activity": False,
                "fruits_diet": False,
                "veggies_diet": True,
                "heavy_alcohol": False,
                "chest_pain_type": 0, # Typical Angina
                "exercise_angina": True,
                "st_depression": 2.6,
                "st_slope": 2, # Downsloping
                "major_vessels": 2,
                "general_health": 5, # Poor
                "physical_health_days": 18,
                "mental_health_days": 10,
                "diff_walking": True,
                "stroke_history": False,
                "heart_disease_history": True,
                "additional_notes": "Patient reports severe crushing retrosternal chest tightness with exertion and shortness of breath."
            },
            "appointment": {
                "date": "2026-10-26",
                "time": "09:00 AM",
                "reason": "Acute exertional angina & severe hypertensive readings",
                "notes": "STAT Priority: Patient flagged for immediate coronary angiography review."
            }
        },
        {
            "user": User(
                email="robert.miller@patient.com",
                hashed_password=default_password,
                full_name="Robert Miller",
                role=UserRole.PATIENT,
                phone_number="+1 (555) 101-2002"
            ),
            "survey": {
                "age": 61,
                "gender": "Male",
                "height_cm": 178.0,
                "weight_kg": 102.0,
                "bmi": 32.2,
                "systolic_bp": 154,
                "diastolic_bp": 94,
                "total_cholesterol": 242,
                "fasting_blood_sugar": 210.0,
                "resting_ecg": 1,
                "max_heart_rate": 128,
                "smoker": True,
                "physical_activity": False,
                "fruits_diet": False,
                "veggies_diet": False,
                "heavy_alcohol": False,
                "chest_pain_type": 1,
                "exercise_angina": False,
                "st_depression": 1.2,
                "st_slope": 1,
                "major_vessels": 1,
                "general_health": 4, # Fair
                "physical_health_days": 12,
                "mental_health_days": 5,
                "diff_walking": True,
                "stroke_history": False,
                "heart_disease_history": False,
                "additional_notes": "Polydipsia, polyuria, recurrent fatigue and numbness in extremities."
            },
            "appointment": {
                "date": "2026-10-27",
                "time": "11:30 AM",
                "reason": "Uncontrolled glycemic levels & high cardiovascular risk consult",
                "notes": "Recommend immediate HbA1c review and dual oral hypoglycemic optimization."
            }
        },
        {
            "user": User(
                email="rachel.adams@patient.com",
                hashed_password=default_password,
                full_name="Rachel Adams",
                role=UserRole.PATIENT,
                phone_number="+1 (555) 101-2003"
            ),
            "survey": {
                "age": 52,
                "gender": "Female",
                "height_cm": 165.0,
                "weight_kg": 76.0,
                "bmi": 27.9,
                "systolic_bp": 136,
                "diastolic_bp": 86,
                "total_cholesterol": 218,
                "fasting_blood_sugar": 115.0,
                "resting_ecg": 0,
                "max_heart_rate": 150,
                "smoker": False,
                "physical_activity": True,
                "fruits_diet": True,
                "veggies_diet": True,
                "heavy_alcohol": False,
                "chest_pain_type": 2, # Non-anginal
                "exercise_angina": False,
                "st_depression": 0.4,
                "st_slope": 0,
                "major_vessels": 0,
                "general_health": 3, # Good
                "physical_health_days": 3,
                "mental_health_days": 4,
                "diff_walking": False,
                "stroke_history": False,
                "heart_disease_history": False,
                "additional_notes": "Occasional palpitations during work stress, seeks dietary consultation."
            },
            "appointment": {
                "date": "2026-11-02",
                "time": "02:00 PM",
                "reason": "Moderate cardiometabolic risk preventive consultation",
                "notes": "Scheduled for Holter telemetry and lipid profile re-evaluation."
            }
        },
        {
            "user": User(
                email="liam.foster@patient.com",
                hashed_password=default_password,
                full_name="Liam Foster",
                role=UserRole.PATIENT,
                phone_number="+1 (555) 101-2004"
            ),
            "survey": {
                "age": 29,
                "gender": "Male",
                "height_cm": 182.0,
                "weight_kg": 74.0,
                "bmi": 22.3,
                "systolic_bp": 118,
                "diastolic_bp": 76,
                "total_cholesterol": 165,
                "fasting_blood_sugar": 88.0,
                "resting_ecg": 0,
                "max_heart_rate": 178,
                "smoker": False,
                "physical_activity": True,
                "fruits_diet": True,
                "veggies_diet": True,
                "heavy_alcohol": False,
                "chest_pain_type": 3, # Asymptomatic
                "exercise_angina": False,
                "st_depression": 0.0,
                "st_slope": 0,
                "major_vessels": 0,
                "general_health": 1, # Excellent
                "physical_health_days": 0,
                "mental_health_days": 1,
                "diff_walking": False,
                "stroke_history": False,
                "heart_disease_history": False,
                "additional_notes": "Annual biometric checkup. Active marathon runner."
            },
            "appointment": {
                "date": "2026-11-15",
                "time": "10:00 AM",
                "reason": "Annual executive preventive health check",
                "notes": "Excellent cardiovascular endurance. Routine wellness confirmation."
            }
        },
        {
            "user": User(
                email="maria.santos@patient.com",
                hashed_password=default_password,
                full_name="Maria Santos",
                role=UserRole.PATIENT,
                phone_number="+1 (555) 101-2005"
            ),
            "survey": {
                "age": 58,
                "gender": "Female",
                "height_cm": 160.0,
                "weight_kg": 85.0,
                "bmi": 33.2,
                "systolic_bp": 162,
                "diastolic_bp": 98,
                "total_cholesterol": 255,
                "fasting_blood_sugar": 168.0,
                "resting_ecg": 1,
                "max_heart_rate": 132,
                "smoker": False,
                "physical_activity": False,
                "fruits_diet": True,
                "veggies_diet": True,
                "heavy_alcohol": False,
                "chest_pain_type": 1, # Atypical
                "exercise_angina": True,
                "st_depression": 1.6,
                "st_slope": 1,
                "major_vessels": 1,
                "general_health": 4,
                "physical_health_days": 8,
                "mental_health_days": 7,
                "diff_walking": True,
                "stroke_history": False,
                "heart_disease_history": False,
                "additional_notes": "Joint stiffness with shortness of breath on stairs."
            },
            "appointment": {
                "date": "2026-10-29",
                "time": "03:30 PM",
                "reason": "High blood pressure follow-up and exertional dyspnea",
                "notes": "Cardiac stress echo recommended."
            }
        }
    ]

    db.add_all([dr_eleanor, dr_marcus, dr_sophia, admin_user])
    db.commit()

    assigned_doctors = [dr_eleanor, dr_marcus, dr_sophia, dr_eleanor, dr_sophia]

    for idx, p_item in enumerate(patients_data):
        user = p_item["user"]
        db.add(user)
        db.commit()
        db.refresh(user)

        s_dict = p_item["survey"]
        survey_record = HealthSurvey(user_id=user.id, **s_dict)
        db.add(survey_record)
        db.commit()
        db.refresh(survey_record)

        # Compute ML & SHAP
        d_score, d_cat, d_conf, d_df = ml_engine.predict_diabetes(s_dict)
        d_base, d_factors, d_summary = shap_service.explain_diabetes(d_df)

        c_score, c_cat, c_conf, c_df = ml_engine.predict_heart(s_dict)
        c_base, c_factors, c_summary = shap_service.explain_heart(c_df)

        urg_score, urg_lvl, urg_breakdown, rec_action = triage_engine.calculate_urgency(
            d_score, c_score, s_dict
        )

        overall_score = round(max(d_score, c_score), 1)
        overall_cat = "Low" if overall_score < 30 else "Medium" if overall_score < 65 else "High"

        prediction_record = RiskPrediction(
            user_id=user.id,
            survey_id=survey_record.id,
            diabetes_risk_score=d_score,
            diabetes_risk_category=d_cat,
            diabetes_confidence=d_conf,
            diabetes_shap_explanation={
                "base_value": d_base,
                "top_factors": d_factors,
                "summary_insight": d_summary
            },
            cardio_risk_score=c_score,
            cardio_risk_category=c_cat,
            cardio_confidence=c_conf,
            cardio_shap_explanation={
                "base_value": c_base,
                "top_factors": c_factors,
                "summary_insight": c_summary
            },
            overall_risk_score=overall_score,
            overall_risk_category=overall_cat,
            urgency_score=urg_score,
            urgency_level=urg_lvl
        )
        db.add(prediction_record)
        db.commit()

        # Seed appointment
        appt_info = p_item["appointment"]
        urg_enum = getattr(UrgencyLevel, urg_lvl.upper(), UrgencyLevel.ROUTINE)
        assigned_doc = assigned_doctors[idx % len(assigned_doctors)]
        appt = Appointment(
            patient_id=user.id,
            doctor_id=assigned_doc.id,
            appointment_date=appt_info["date"],
            appointment_time=appt_info["time"],
            reason=appt_info["reason"],
            symptoms_summary=s_dict.get("additional_notes"),
            urgency_score=urg_score,
            urgency_level=urg_enum,
            status=AppointmentStatus.CONFIRMED if urg_score > 50 else AppointmentStatus.PENDING,
            doctor_notes=appt_info["notes"]
        )
        db.add(appt)
        db.commit()

        print(f"Seeded Patient: {user.full_name} | Risk: {overall_score}% ({overall_cat}) | Urgency: {urg_score} ({urg_lvl})")

    db.close()
    print("--------------------------------------------------")
    print("Database seeding completed successfully!")
    print("Doctors: dr.eleanor@hospital.org / dr.marcus@hospital.org / dr.sophia@hospital.org (pw: password123)")
    print("Admin: admin@hospital.org (pw: admin123)")
    print("Patients: arthur.pendelton@patient.com / robert.miller@patient.com / rachel.adams@patient.com / liam.foster@patient.com / maria.santos@patient.com (pw: password123)")

if __name__ == "__main__":
    seed_database()
