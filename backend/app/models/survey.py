from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class HealthSurvey(Base):
    __tablename__ = "health_surveys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Demographics
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False) # 'Male', 'Female', 'Other'
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    bmi = Column(Float, nullable=False)

    # Vitals & Labs
    systolic_bp = Column(Integer, nullable=False)       # resting bp (trestbps)
    diastolic_bp = Column(Integer, nullable=False)
    total_cholesterol = Column(Integer, nullable=False)  # chol in mg/dl
    fasting_blood_sugar = Column(Float, nullable=False)  # mg/dl
    resting_ecg = Column(Integer, default=0)            # 0: Normal, 1: ST-T wave, 2: LVH
    max_heart_rate = Column(Integer, nullable=False)     # thalach (bpm)

    # Lifestyle
    smoker = Column(Boolean, default=False)
    physical_activity = Column(Boolean, default=True)   # regular physical activity
    fruits_diet = Column(Boolean, default=True)         # fruits consumed >= 1x / day
    veggies_diet = Column(Boolean, default=True)        # veggies consumed >= 1x / day
    heavy_alcohol = Column(Boolean, default=False)      # heavy alcohol consumption
    
    # Symptoms & Clinical History
    chest_pain_type = Column(Integer, default=0)        # 0: Typical Angina, 1: Atypical Angina, 2: Non-anginal, 3: Asymptomatic
    exercise_angina = Column(Boolean, default=False)    # exercise induced angina (1/0)
    st_depression = Column(Float, default=0.0)          # oldpeak
    st_slope = Column(Integer, default=1)               # 0: Up, 1: Flat, 2: Down
    major_vessels = Column(Integer, default=0)          # 0-3 ca vessels
    general_health = Column(Integer, default=2)         # 1: Excellent, 2: Very Good, 3: Good, 4: Fair, 5: Poor
    physical_health_days = Column(Integer, default=0)   # bad days in past 30 days
    mental_health_days = Column(Integer, default=0)     # bad days in past 30 days
    diff_walking = Column(Boolean, default=False)       # difficulty walking
    stroke_history = Column(Boolean, default=False)     # history of stroke
    heart_disease_history = Column(Boolean, default=False) # history of myocardial infarction / CAD
    
    additional_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    user = relationship("User", back_populates="surveys")
    prediction = relationship("RiskPrediction", back_populates="survey", uselist=False, cascade="all, delete-orphan")
