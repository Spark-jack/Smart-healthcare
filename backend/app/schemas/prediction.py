from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from datetime import datetime

class ShapFactor(BaseModel):
    feature: str
    feature_label: str
    shap_value: float
    feature_value: Any
    impact: str # "increases_risk" or "decreases_risk"
    interpretation: str

class DiseasePredictionOut(BaseModel):
    disease_name: str
    risk_score: float             # Calibrated probability: 0 - 100%
    risk_category: str            # Low, Medium, High
    confidence: float             # 0.0 - 1.0 (calibrated confidence score)
    uncertainty_interval: Optional[List[float]] = None # [low%, high%] 95% plausible range
    expected_calibration_error: Optional[float] = None
    data_source: Optional[str] = None # "real" or "synthetic_demo"
    data_quality_warning: Optional[str] = None
    base_value: float
    top_factors: List[ShapFactor]
    summary_insight: str

class PredictionResultOut(BaseModel):
    id: int
    user_id: int
    survey_id: int
    diabetes: DiseasePredictionOut
    cardiovascular: DiseasePredictionOut
    overall_risk_score: float
    overall_risk_category: str
    urgency_score: float
    urgency_level: str
    recommended_action: str
    data_quality_warning: Optional[str] = None
    data_source: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
