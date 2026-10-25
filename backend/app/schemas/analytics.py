from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class RiskDistributionItem(BaseModel):
    category: str # "Low", "Medium", "High"
    count: int
    percentage: float

class AgeGroupRisk(BaseModel):
    age_group: str # e.g. "18-35", "36-50", "51-65", "65+"
    low_risk: int
    medium_risk: int
    high_risk: int

class CommonFactorStat(BaseModel):
    factor_name: str
    prevalence_pct: float
    avg_risk_increase: float

class UrgencyLoadItem(BaseModel):
    urgency_level: str
    count: int

class DoctorAlert(BaseModel):
    patient_id: int
    patient_name: str
    survey_id: int
    prediction_id: int
    overall_risk_score: float
    urgency_level: str
    key_drivers: List[str]
    alert_time: str
    is_critical: bool

class PopulationInsights(BaseModel):
    total_patients: int
    high_risk_count: int
    critical_triage_count: int
    avg_diabetes_risk: float
    avg_cardio_risk: float
    risk_distribution: List[RiskDistributionItem]
    age_group_risks: List[AgeGroupRisk]
    common_risk_factors: List[CommonFactorStat]
    urgency_load: List[UrgencyLoadItem]
    recent_alerts: List[DoctorAlert]

class TrendPeriodItem(BaseModel):
    period: str
    predictions_count: int
    avg_diabetes_risk: float
    avg_cardio_risk: float
    high_critical_count: int
    critical_count: int = 0
    high_count: int = 0
    moderate_count: int = 0
    routine_count: int = 0
    new_patients: int

class TrendAnalyticsOut(BaseModel):
    period_type: str # "week" or "month"
    total_predictions: int
    total_new_patients: int
    overall_avg_diabetes_risk: float
    overall_avg_cardio_risk: float
    total_high_critical: int
    periods: List[TrendPeriodItem]
