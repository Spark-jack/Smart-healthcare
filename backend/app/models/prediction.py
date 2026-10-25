from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    survey_id = Column(Integer, ForeignKey("health_surveys.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Diabetes Prediction
    diabetes_risk_score = Column(Float, nullable=False)       # 0.0 to 100.0%
    diabetes_risk_category = Column(String(50), nullable=False) # Low, Medium, High
    diabetes_confidence = Column(Float, nullable=False)        # 0.0 to 1.0
    diabetes_shap_explanation = Column(JSON, nullable=False)   # Top positive & negative drivers

    # Cardiovascular Prediction
    cardio_risk_score = Column(Float, nullable=False)         # 0.0 to 100.0%
    cardio_risk_category = Column(String(50), nullable=False)   # Low, Medium, High
    cardio_confidence = Column(Float, nullable=False)          # 0.0 to 1.0
    cardio_shap_explanation = Column(JSON, nullable=False)     # Top positive & negative drivers

    # Overall Combined Assessment & Triage
    overall_risk_score = Column(Float, nullable=False)        # max or weighted risk
    overall_risk_category = Column(String(50), nullable=False)  # Low, Medium, High
    urgency_score = Column(Float, nullable=False)             # 0 to 100
    urgency_level = Column(String(50), nullable=False)         # Routine, Moderate, High, Critical

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="predictions")
    survey = relationship("HealthSurvey", back_populates="prediction")
