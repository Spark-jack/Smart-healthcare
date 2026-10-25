from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_patient
from app.models.user import User
from app.models.survey import HealthSurvey
from app.models.prediction import RiskPrediction
from app.schemas.survey import SurveyCreate, SurveyOut
from app.schemas.prediction import PredictionResultOut, DiseasePredictionOut
from app.services.ml_engine import ml_engine
from app.services.shap_explainer import shap_service
from app.services.triage_engine import triage_engine
from app.services.notification_service import notification_service

router = APIRouter(prefix="/surveys", tags=["Health Surveys & Predictive Intake"])

@router.post("/", response_model=PredictionResultOut, status_code=status.HTTP_201_CREATED)
def submit_health_survey(
    survey_in: SurveyCreate,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    survey_data = survey_in.model_dump()

    # Track prior risk category for RISK_UPDATED notifications
    prev_pred = db.query(RiskPrediction).filter(
        RiskPrediction.user_id == current_user.id
    ).order_by(RiskPrediction.created_at.desc()).first()
    prev_category = prev_pred.overall_risk_category if prev_pred else None

    # Calculate BMI if not provided
    height_m = survey_data["height_cm"] / 100.0
    weight_kg = survey_data["weight_kg"]
    calculated_bmi = round(weight_kg / (height_m ** 2), 1)
    if not survey_data.get("bmi"):
        survey_data["bmi"] = calculated_bmi

    # Save Survey record
    survey_record = HealthSurvey(
        user_id=current_user.id,
        **survey_data
    )
    db.add(survey_record)
    db.commit()
    db.refresh(survey_record)

    # 1. Run Calibrated Diabetes Prediction & SHAP
    d_res = ml_engine.predict_diabetes(survey_data)
    d_score, d_cat, d_conf, d_df = d_res
    d_base, d_factors, d_summary = shap_service.explain_diabetes(d_df)

    # 2. Run Calibrated Cardiovascular Prediction & SHAP
    c_res = ml_engine.predict_heart(survey_data)
    c_score, c_cat, c_conf, c_df = c_res
    c_base, c_factors, c_summary = shap_service.explain_heart(c_df)

    # 3. Urgency scoring
    urgency_score, urgency_level, triage_breakdown, rec_action = triage_engine.calculate_urgency(
        d_score, c_score, survey_data
    )

    # Combined risk score (weighted maximum)
    overall_score = round(max(d_score, c_score), 1)
    if overall_score < 30.0:
        overall_cat = "Low"
    elif overall_score < 65.0:
        overall_cat = "Medium"
    else:
        overall_cat = "High"

    quality_warning = d_res.data_quality_warning or c_res.data_quality_warning
    data_source = d_res.data_source

    # Save Prediction record with extended explanation JSON
    prediction_record = RiskPrediction(
        user_id=current_user.id,
        survey_id=survey_record.id,
        diabetes_risk_score=d_score,
        diabetes_risk_category=d_cat,
        diabetes_confidence=d_conf,
        diabetes_shap_explanation={
            "base_value": d_base,
            "top_factors": d_factors,
            "summary_insight": d_summary,
            "uncertainty_interval": d_res.uncertainty_interval,
            "data_quality_warning": d_res.data_quality_warning,
            "data_source": d_res.data_source,
            "expected_calibration_error": d_res.ece
        },
        cardio_risk_score=c_score,
        cardio_risk_category=c_cat,
        cardio_confidence=c_conf,
        cardio_shap_explanation={
            "base_value": c_base,
            "top_factors": c_factors,
            "summary_insight": c_summary,
            "uncertainty_interval": c_res.uncertainty_interval,
            "data_quality_warning": c_res.data_quality_warning,
            "data_source": c_res.data_source,
            "expected_calibration_error": c_res.ece
        },
        overall_risk_score=overall_score,
        overall_risk_category=overall_cat,
        urgency_score=urgency_score,
        urgency_level=urgency_level
    )
    db.add(prediction_record)
    db.commit()
    db.refresh(prediction_record)

    # Dispatch Service Layer Notifications
    # a) HIGH_RISK_FLAG when urgency is Critical or High
    if urgency_level in ("Critical", "High"):
        notification_service.notify_high_risk_flag(db, current_user, prediction_record)

    # b) RISK_UPDATED when new survey produces a materially different category
    if prev_category and prev_category != overall_cat:
        notification_service.notify_risk_updated(db, current_user, prev_category, overall_cat, prediction_record)

    return PredictionResultOut(
        id=prediction_record.id,
        user_id=current_user.id,
        survey_id=survey_record.id,
        diabetes=DiseasePredictionOut(
            disease_name="Diabetes",
            risk_score=d_score,
            risk_category=d_cat,
            confidence=d_conf,
            uncertainty_interval=d_res.uncertainty_interval,
            expected_calibration_error=d_res.ece,
            data_source=d_res.data_source,
            data_quality_warning=d_res.data_quality_warning,
            base_value=d_base,
            top_factors=d_factors,
            summary_insight=d_summary
        ),
        cardiovascular=DiseasePredictionOut(
            disease_name="Cardiovascular Disease",
            risk_score=c_score,
            risk_category=c_cat,
            confidence=c_conf,
            uncertainty_interval=c_res.uncertainty_interval,
            expected_calibration_error=c_res.ece,
            data_source=c_res.data_source,
            data_quality_warning=c_res.data_quality_warning,
            base_value=c_base,
            top_factors=c_factors,
            summary_insight=c_summary
        ),
        overall_risk_score=overall_score,
        overall_risk_category=overall_cat,
        urgency_score=urgency_score,
        urgency_level=urgency_level,
        recommended_action=rec_action,
        data_quality_warning=quality_warning,
        data_source=data_source,
        created_at=prediction_record.created_at
    )

@router.get("/latest", response_model=SurveyOut)
def get_latest_survey(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    survey = db.query(HealthSurvey).filter(HealthSurvey.user_id == current_user.id).order_by(HealthSurvey.created_at.desc()).first()
    if not survey:
        raise HTTPException(status_code=404, detail="No health survey found for this patient.")
    return survey

@router.get("/history", response_model=List[SurveyOut])
def get_survey_history(
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db)
):
    surveys = db.query(HealthSurvey).filter(HealthSurvey.user_id == current_user.id).order_by(HealthSurvey.created_at.desc()).all()
    return surveys
