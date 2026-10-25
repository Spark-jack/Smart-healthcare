from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_doctor
from app.models.user import User, UserRole
from app.models.prediction import RiskPrediction
from app.schemas.prediction import PredictionResultOut, DiseasePredictionOut

router = APIRouter(prefix="/predictions", tags=["Risk Predictions & Explainable AI"])

def _format_prediction_out(pred: RiskPrediction) -> PredictionResultOut:
    d_shap = pred.diabetes_shap_explanation or {}
    c_shap = pred.cardio_shap_explanation or {}

    # Map timeframe from urgency level
    timeframe_map = {
        "Critical": "Immediate evaluation within 24 Hours",
        "High": "Priority consult within 48 to 72 Hours",
        "Moderate": "Clinical Review within 1 to 2 Weeks",
        "Routine": "Routine Check-up within 3 to 4 Weeks"
    }

    # Extract calibration and uncertainty metadata
    d_interval = d_shap.get("uncertainty_interval") or [
        round(max(0.0, pred.diabetes_risk_score - 6.5), 1),
        round(min(100.0, pred.diabetes_risk_score + 6.5), 1)
    ]
    c_interval = c_shap.get("uncertainty_interval") or [
        round(max(0.0, pred.cardio_risk_score - 8.0), 1),
        round(min(100.0, pred.cardio_risk_score + 8.0), 1)
    ]
    data_source = d_shap.get("data_source") or c_shap.get("data_source") or "real"
    quality_warning = d_shap.get("data_quality_warning") or c_shap.get("data_quality_warning")

    return PredictionResultOut(
        id=pred.id,
        user_id=pred.user_id,
        survey_id=pred.survey_id,
        diabetes=DiseasePredictionOut(
            disease_name="Diabetes",
            risk_score=pred.diabetes_risk_score,
            risk_category=pred.diabetes_risk_category,
            confidence=pred.diabetes_confidence,
            uncertainty_interval=d_interval,
            expected_calibration_error=d_shap.get("expected_calibration_error", 0.0038),
            data_source=d_shap.get("data_source", "real"),
            data_quality_warning=d_shap.get("data_quality_warning"),
            base_value=d_shap.get("base_value", 0.0),
            top_factors=d_shap.get("top_factors", []),
            summary_insight=d_shap.get("summary_insight", "Evaluation completed.")
        ),
        cardiovascular=DiseasePredictionOut(
            disease_name="Cardiovascular Disease",
            risk_score=pred.cardio_risk_score,
            risk_category=pred.cardio_risk_category,
            confidence=pred.cardio_confidence,
            uncertainty_interval=c_interval,
            expected_calibration_error=c_shap.get("expected_calibration_error", 0.1106),
            data_source=c_shap.get("data_source", "real"),
            data_quality_warning=c_shap.get("data_quality_warning"),
            base_value=c_shap.get("base_value", 0.0),
            top_factors=c_shap.get("top_factors", []),
            summary_insight=c_shap.get("summary_insight", "Evaluation completed.")
        ),
        overall_risk_score=pred.overall_risk_score,
        overall_risk_category=pred.overall_risk_category,
        urgency_score=pred.urgency_score,
        urgency_level=pred.urgency_level,
        recommended_action=timeframe_map.get(pred.urgency_level, "Routine Monitoring"),
        data_quality_warning=quality_warning,
        data_source=data_source,
        created_at=pred.created_at
    )

@router.get("/latest", response_model=PredictionResultOut)
def get_latest_prediction(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    pred = db.query(RiskPrediction).filter(RiskPrediction.user_id == current_user.id).order_by(RiskPrediction.created_at.desc()).first()
    if not pred:
        raise HTTPException(status_code=404, detail="No risk predictions found for this user.")
    return _format_prediction_out(pred)

@router.get("/history", response_model=List[PredictionResultOut])
def get_prediction_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    preds = db.query(RiskPrediction).filter(RiskPrediction.user_id == current_user.id).order_by(RiskPrediction.created_at.asc()).all()
    return [_format_prediction_out(p) for p in preds]

@router.get("/patient/{patient_id}", response_model=List[PredictionResultOut])
def get_patient_predictions_for_doctor(
    patient_id: int,
    current_user: User = Depends(require_doctor),
    db: Session = Depends(get_db)
):
    preds = db.query(RiskPrediction).filter(RiskPrediction.user_id == patient_id).order_by(RiskPrediction.created_at.desc()).all()
    return [_format_prediction_out(p) for p in preds]
