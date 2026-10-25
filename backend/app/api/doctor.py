from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import require_doctor
from app.models.user import User, UserRole
from app.models.survey import HealthSurvey
from app.models.prediction import RiskPrediction
from app.models.appointment import Appointment, UrgencyLevel
from app.schemas.analytics import (
    PopulationInsights, RiskDistributionItem, AgeGroupRisk, 
    CommonFactorStat, UrgencyLoadItem, DoctorAlert,
    TrendPeriodItem, TrendAnalyticsOut
)

router = APIRouter(prefix="/doctor", tags=["Doctor Clinical Dashboard & Analytics"])

@router.get("/patients/triage-queue")
def get_triage_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Returns prioritized patient triage queue sorted by Urgency Score and Overall Risk.
    """
    # Fetch latest prediction for each patient
    patients = db.query(User).filter(User.role == UserRole.PATIENT).all()
    queue = []

    for patient in patients:
        latest_pred = db.query(RiskPrediction).filter(
            RiskPrediction.user_id == patient.id
        ).order_by(RiskPrediction.created_at.desc()).first()

        latest_survey = db.query(HealthSurvey).filter(
            HealthSurvey.user_id == patient.id
        ).order_by(HealthSurvey.created_at.desc()).first()

        latest_appt = db.query(Appointment).filter(
            Appointment.patient_id == patient.id
        ).order_by(Appointment.created_at.desc()).first()

        if latest_pred and latest_survey:
            # Extract top driver for quick display
            cardio_factors = latest_pred.cardio_shap_explanation.get("top_factors", [])
            diabetes_factors = latest_pred.diabetes_shap_explanation.get("top_factors", [])
            top_concern = None
            if latest_pred.overall_risk_score > 30:
                candidates = [f["feature_label"] for f in cardio_factors + diabetes_factors if f.get("impact") == "increases_risk"]
                top_concern = candidates[0] if candidates else "Elevated Combined Metrics"

            queue.append({
                "patient_id": patient.id,
                "patient_name": patient.full_name,
                "email": patient.email,
                "age": latest_survey.age,
                "gender": latest_survey.gender,
                "bmi": latest_survey.bmi,
                "systolic_bp": latest_survey.systolic_bp,
                "overall_risk_score": latest_pred.overall_risk_score,
                "overall_risk_category": latest_pred.overall_risk_category,
                "diabetes_risk_score": latest_pred.diabetes_risk_score,
                "diabetes_risk_category": latest_pred.diabetes_risk_category,
                "cardio_risk_score": latest_pred.cardio_risk_score,
                "cardio_risk_category": latest_pred.cardio_risk_category,
                "urgency_score": latest_pred.urgency_score,
                "urgency_level": latest_pred.urgency_level,
                "top_concern": top_concern or "Routine Baseline",
                "last_assessed": latest_pred.created_at.strftime("%Y-%m-%d %H:%M"),
                "appointment_status": latest_appt.status.value if latest_appt else "None Scheduled"
            })

    # Sort descending by urgency_score, then overall_risk_score
    queue.sort(key=lambda x: (x["urgency_score"], x["overall_risk_score"]), reverse=True)
    return queue

@router.get("/patients/{patient_id}/deep-dive")
def get_patient_deep_dive(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.PATIENT).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    surveys = db.query(HealthSurvey).filter(HealthSurvey.user_id == patient_id).order_by(HealthSurvey.created_at.asc()).all()
    predictions = db.query(RiskPrediction).filter(RiskPrediction.user_id == patient_id).order_by(RiskPrediction.created_at.asc()).all()
    appointments = db.query(Appointment).filter(Appointment.patient_id == patient_id).order_by(Appointment.created_at.desc()).all()

    # Build longitudinal risk trajectory
    trajectory = []
    for p in predictions:
        trajectory.append({
            "date": p.created_at.strftime("%b %d, %Y"),
            "diabetes_risk": p.diabetes_risk_score,
            "cardio_risk": p.cardio_risk_score,
            "overall_risk": p.overall_risk_score,
            "urgency_score": p.urgency_score
        })

    latest_pred = predictions[-1] if predictions else None
    latest_survey = surveys[-1] if surveys else None

    return {
        "patient": {
            "id": patient.id,
            "name": patient.full_name,
            "email": patient.email,
            "phone": patient.phone_number
        },
        "latest_vitals": {
            "age": latest_survey.age if latest_survey else None,
            "gender": latest_survey.gender if latest_survey else None,
            "bmi": latest_survey.bmi if latest_survey else None,
            "blood_pressure": f"{latest_survey.systolic_bp}/{latest_survey.diastolic_bp} mmHg" if latest_survey else None,
            "cholesterol": f"{latest_survey.total_cholesterol} mg/dL" if latest_survey else None,
            "fasting_glucose": f"{latest_survey.fasting_blood_sugar} mg/dL" if latest_survey else None,
            "max_heart_rate": f"{latest_survey.max_heart_rate} bpm" if latest_survey else None,
            "smoker": "Yes" if latest_survey and latest_survey.smoker else "No",
            "chest_pain_type": latest_survey.chest_pain_type if latest_survey else None,
            "st_depression": latest_survey.st_depression if latest_survey else None
        },
        "latest_prediction": {
            "overall_risk_score": latest_pred.overall_risk_score if latest_pred else 0,
            "overall_risk_category": latest_pred.overall_risk_category if latest_pred else "Low",
            "urgency_score": latest_pred.urgency_score if latest_pred else 0,
            "urgency_level": latest_pred.urgency_level if latest_pred else "Routine",
            "diabetes": {
                "score": latest_pred.diabetes_risk_score if latest_pred else 0,
                "category": latest_pred.diabetes_risk_category if latest_pred else "Low",
                "shap": latest_pred.diabetes_shap_explanation if latest_pred else {}
            },
            "cardio": {
                "score": latest_pred.cardio_risk_score if latest_pred else 0,
                "category": latest_pred.cardio_risk_category if latest_pred else "Low",
                "shap": latest_pred.cardio_shap_explanation if latest_pred else {}
            }
        },
        "trajectory": trajectory,
        "appointments": [
            {
                "id": a.id,
                "date": a.appointment_date,
                "time": a.appointment_time,
                "reason": a.reason,
                "status": a.status.value,
                "urgency_level": a.urgency_level.value,
                "notes": a.doctor_notes
            } for a in appointments
        ]
    }

@router.get("/analytics/population", response_model=PopulationInsights)
def get_population_insights(
    age_group: Optional[str] = Query(None),
    sex: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    survey_query = db.query(HealthSurvey)
    
    # Apply demographic filters
    if age_group:
        if age_group == "18-35":
            survey_query = survey_query.filter(HealthSurvey.age.between(18, 35))
        elif age_group == "36-50":
            survey_query = survey_query.filter(HealthSurvey.age.between(36, 50))
        elif age_group == "51-65":
            survey_query = survey_query.filter(HealthSurvey.age.between(51, 65))
        elif age_group == "65+":
            survey_query = survey_query.filter(HealthSurvey.age >= 65)

    if sex is not None and str(sex).strip():
        s = str(sex).strip().lower()
        if s in ("1", "male", "m"):
            survey_query = survey_query.filter(func.lower(HealthSurvey.gender).like("%male%") & ~func.lower(HealthSurvey.gender).like("%female%"))
        elif s in ("0", "female", "f"):
            survey_query = survey_query.filter(func.lower(HealthSurvey.gender).like("%female%"))

    surveys = survey_query.all()
    survey_ids = [s.id for s in surveys]

    pred_query = db.query(RiskPrediction)
    if age_group or sex:
        pred_query = pred_query.filter(RiskPrediction.survey_id.in_(survey_ids))
    preds = pred_query.all()

    appts = db.query(Appointment).all()

    user_query = db.query(User).filter(User.role == UserRole.PATIENT)
    total_patients = user_query.count()

    if not preds:
        return PopulationInsights(
            total_patients=total_patients if not (age_group or sex) else len(set(s.user_id for s in surveys)),
            high_risk_count=0,
            critical_triage_count=0,
            avg_diabetes_risk=0.0,
            avg_cardio_risk=0.0,
            risk_distribution=[],
            age_group_risks=[],
            common_risk_factors=[],
            urgency_load=[],
            recent_alerts=[]
        )

    high_risk_count = sum(1 for p in preds if p.overall_risk_category == "High")
    critical_triage_count = sum(1 for p in preds if p.urgency_level in ["Critical", "High"])
    avg_diabetes = round(sum(p.diabetes_risk_score for p in preds) / len(preds), 1)
    avg_cardio = round(sum(p.cardio_risk_score for p in preds) / len(preds), 1)

    # Risk Distribution
    low_c = sum(1 for p in preds if p.overall_risk_category == "Low")
    med_c = sum(1 for p in preds if p.overall_risk_category == "Medium")
    high_c = sum(1 for p in preds if p.overall_risk_category == "High")
    total_preds = len(preds)
    risk_dist = [
        RiskDistributionItem(category="Low Risk (<30%)", count=low_c, percentage=round(low_c / total_preds * 100, 1)),
        RiskDistributionItem(category="Medium Risk (30-65%)", count=med_c, percentage=round(med_c / total_preds * 100, 1)),
        RiskDistributionItem(category="High Risk (>65%)", count=high_c, percentage=round(high_c / total_preds * 100, 1)),
    ]

    # Age Group Risk Breakdown
    age_bins = {"18-35": [0, 0, 0], "36-50": [0, 0, 0], "51-65": [0, 0, 0], "65+": [0, 0, 0]}
    for s in surveys:
        if not s.prediction:
            continue
        age = s.age
        grp = "18-35" if age < 36 else "36-50" if age <= 50 else "51-65" if age <= 65 else "65+"
        cat = s.prediction.overall_risk_category
        idx = 0 if cat == "Low" else 1 if cat == "Medium" else 2
        age_bins[grp][idx] += 1

    age_group_risks = [
        AgeGroupRisk(age_group=k, low_risk=v[0], medium_risk=v[1], high_risk=v[2])
        for k, v in age_bins.items()
    ]

    # Common Risk Factors
    smokers = sum(1 for s in surveys if s.smoker)
    high_bp = sum(1 for s in surveys if s.systolic_bp >= 140)
    high_chol = sum(1 for s in surveys if s.total_cholesterol >= 200)
    sedentary = sum(1 for s in surveys if not s.physical_activity)
    obese = sum(1 for s in surveys if s.bmi >= 30)
    n_surv = max(1, len(surveys))

    common_factors = [
        CommonFactorStat(factor_name="Hypertension (BP >= 140)", prevalence_pct=round(high_bp / n_surv * 100, 1), avg_risk_increase=22.4),
        CommonFactorStat(factor_name="Elevated Cholesterol (>= 200 mg/dL)", prevalence_pct=round(high_chol / n_surv * 100, 1), avg_risk_increase=18.6),
        CommonFactorStat(factor_name="Obesity (BMI >= 30)", prevalence_pct=round(obese / n_surv * 100, 1), avg_risk_increase=16.8),
        CommonFactorStat(factor_name="Sedentary Lifestyle", prevalence_pct=round(sedentary / n_surv * 100, 1), avg_risk_increase=12.2),
        CommonFactorStat(factor_name="Active Tobacco Smoking", prevalence_pct=round(smokers / n_surv * 100, 1), avg_risk_increase=15.0),
    ]

    # Urgency Load
    urg_counts = {"Critical": 0, "High": 0, "Moderate": 0, "Routine": 0}
    for a in appts:
        lvl = a.urgency_level.value
        urg_counts[lvl] = urg_counts.get(lvl, 0) + 1

    urgency_load = [UrgencyLoadItem(urgency_level=k, count=v) for k, v in urg_counts.items()]

    # Critical Alerts
    critical_preds = db.query(RiskPrediction).filter(
        RiskPrediction.urgency_level.in_(["Critical", "High"])
    ).order_by(RiskPrediction.created_at.desc()).limit(8).all()

    alerts = []
    for cp in critical_preds:
        user = cp.user
        factors = []
        if cp.cardio_shap_explanation:
            factors += [f["feature_label"] for f in cp.cardio_shap_explanation.get("top_factors", []) if f.get("impact") == "increases_risk"]
        if cp.diabetes_shap_explanation:
            factors += [f["feature_label"] for f in cp.diabetes_shap_explanation.get("top_factors", []) if f.get("impact") == "increases_risk"]

        alerts.append(DoctorAlert(
            patient_id=user.id if user else 0,
            patient_name=user.full_name if user else "Unknown Patient",
            survey_id=cp.survey_id,
            prediction_id=cp.id,
            overall_risk_score=cp.overall_risk_score,
            urgency_level=cp.urgency_level,
            key_drivers=factors[:2] or ["Critical Triage Metrics"],
            alert_time=cp.created_at.strftime("%b %d, %H:%M"),
            is_critical=(cp.urgency_level == "Critical")
        ))

    return PopulationInsights(
        total_patients=total_patients if not (age_group or sex) else len(set(s.user_id for s in surveys)),
        high_risk_count=high_risk_count,
        critical_triage_count=critical_triage_count,
        avg_diabetes_risk=avg_diabetes,
        avg_cardio_risk=avg_cardio,
        risk_distribution=risk_dist,
        age_group_risks=age_group_risks,
        common_risk_factors=common_factors,
        urgency_load=urgency_load,
        recent_alerts=alerts
    )

@router.get("/analytics/trends", response_model=TrendAnalyticsOut)
def get_population_trends(
    period: str = Query("month", regex="^(week|month)$"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    age_group: Optional[str] = Query(None),
    sex: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_doctor)
):
    """
    Returns population-level longitudinal trends grouped by week or month using SQL aggregations.
    """
    is_sqlite = "sqlite" in str(db.bind.url) if db.bind else True
    if is_sqlite:
        if period == "week":
            period_col = func.strftime('%Y-W%W', RiskPrediction.created_at)
            user_period_col = func.strftime('%Y-W%W', User.created_at)
        else:
            period_col = func.strftime('%Y-%m', RiskPrediction.created_at)
            user_period_col = func.strftime('%Y-%m', User.created_at)
    else:
        if period == "week":
            period_col = func.to_char(RiskPrediction.created_at, 'IYYY-"W"IW')
            user_period_col = func.to_char(User.created_at, 'IYYY-"W"IW')
        else:
            period_col = func.to_char(RiskPrediction.created_at, 'YYYY-MM')
            user_period_col = func.to_char(User.created_at, 'YYYY-MM')

    # Base query for predictions aggregated per period
    pred_query = db.query(
        period_col.label("period"),
        func.count(RiskPrediction.id).label("predictions_count"),
        func.avg(RiskPrediction.diabetes_risk_score).label("avg_diabetes_risk"),
        func.avg(RiskPrediction.cardio_risk_score).label("avg_cardio_risk"),
        func.sum(case((RiskPrediction.urgency_level.in_(["Critical", "High"]), 1), else_=0)).label("high_critical_count"),
        func.sum(case((RiskPrediction.urgency_level == "Critical", 1), else_=0)).label("critical_count"),
        func.sum(case((RiskPrediction.urgency_level == "High", 1), else_=0)).label("high_count"),
        func.sum(case((RiskPrediction.urgency_level == "Moderate", 1), else_=0)).label("moderate_count"),
        func.sum(case((RiskPrediction.urgency_level == "Routine", 1), else_=0)).label("routine_count")
    ).join(HealthSurvey, RiskPrediction.survey_id == HealthSurvey.id)

    # Date filters
    if from_date:
        pred_query = pred_query.filter(RiskPrediction.created_at >= from_date)
    if to_date:
        pred_query = pred_query.filter(RiskPrediction.created_at <= f"{to_date} 23:59:59")

    # Demographic filters
    if age_group:
        if age_group == "18-35":
            pred_query = pred_query.filter(HealthSurvey.age.between(18, 35))
        elif age_group == "36-50":
            pred_query = pred_query.filter(HealthSurvey.age.between(36, 50))
        elif age_group == "51-65":
            pred_query = pred_query.filter(HealthSurvey.age.between(51, 65))
        elif age_group == "65+":
            pred_query = pred_query.filter(HealthSurvey.age >= 65)

    if sex is not None and str(sex).strip():
        s = str(sex).strip().lower()
        if s in ("1", "male", "m"):
            pred_query = pred_query.filter(func.lower(HealthSurvey.gender).like("%male%") & ~func.lower(HealthSurvey.gender).like("%female%"))
        elif s in ("0", "female", "f"):
            pred_query = pred_query.filter(func.lower(HealthSurvey.gender).like("%female%"))

    pred_groups = pred_query.group_by(period_col).order_by(period_col.asc()).all()

    # Query new patients registered per period
    user_query = db.query(
        user_period_col.label("period"),
        func.count(User.id).label("new_patients")
    ).filter(User.role == UserRole.PATIENT)

    if from_date:
        user_query = user_query.filter(User.created_at >= from_date)
    if to_date:
        user_query = user_query.filter(User.created_at <= f"{to_date} 23:59:59")

    user_groups = {row.period: row.new_patients for row in user_query.group_by(user_period_col).all()}

    # Merge groups
    all_periods = sorted(list(set([r.period for r in pred_groups if r.period] + list(user_groups.keys()))))
    pred_dict = {r.period: r for r in pred_groups}

    trend_items = []
    total_preds = 0
    total_high_critical = 0
    total_diabetes_sum = 0.0
    total_cardio_sum = 0.0

    for p in all_periods:
        r = pred_dict.get(p)
        new_pts = user_groups.get(p, 0)
        p_count = int(r.predictions_count) if r else 0
        p_avg_d = round(float(r.avg_diabetes_risk), 1) if (r and r.avg_diabetes_risk is not None) else 0.0
        p_avg_c = round(float(r.avg_cardio_risk), 1) if (r and r.avg_cardio_risk is not None) else 0.0
        p_hc = int(r.high_critical_count) if (r and r.high_critical_count is not None) else 0
        p_crit = int(r.critical_count) if (r and r.critical_count is not None) else 0
        p_hi = int(r.high_count) if (r and r.high_count is not None) else 0
        p_mod = int(r.moderate_count) if (r and r.moderate_count is not None) else 0
        p_rout = int(r.routine_count) if (r and r.routine_count is not None) else 0

        total_preds += p_count
        total_high_critical += p_hc
        if r and r.avg_diabetes_risk is not None:
            total_diabetes_sum += float(r.avg_diabetes_risk) * p_count
        if r and r.avg_cardio_risk is not None:
            total_cardio_sum += float(r.avg_cardio_risk) * p_count

        trend_items.append(TrendPeriodItem(
            period=p,
            predictions_count=p_count,
            avg_diabetes_risk=p_avg_d,
            avg_cardio_risk=p_avg_c,
            high_critical_count=p_hc,
            critical_count=p_crit,
            high_count=p_hi,
            moderate_count=p_mod,
            routine_count=p_rout,
            new_patients=new_pts
        ))

    overall_avg_d = round(total_diabetes_sum / total_preds, 1) if total_preds > 0 else 0.0
    overall_avg_c = round(total_cardio_sum / total_preds, 1) if total_preds > 0 else 0.0
    
    # Calculate total patient count
    if not from_date and not to_date and not age_group and not sex:
        total_patients = db.query(User).filter(User.role == UserRole.PATIENT).count()
    else:
        total_patients = sum(user_groups.values()) if user_groups else 0

    return TrendAnalyticsOut(
        period_type=period,
        total_predictions=total_preds,
        total_new_patients=total_patients,
        overall_avg_diabetes_risk=overall_avg_d,
        overall_avg_cardio_risk=overall_avg_c,
        total_high_critical=total_high_critical,
        periods=trend_items
    )
