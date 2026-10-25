from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SurveyBase(BaseModel):
    # Demographics
    age: int = Field(..., ge=1, le=120, description="Age in years")
    gender: str = Field(..., description="'Male', 'Female', or 'Other'")
    height_cm: float = Field(..., ge=50, le=250, description="Height in centimeters")
    weight_kg: float = Field(..., ge=20, le=300, description="Weight in kilograms")
    bmi: Optional[float] = None # Calculated automatically if not provided

    # Vitals & Labs
    systolic_bp: int = Field(..., ge=60, le=250, description="Resting systolic BP (mmHg)")
    diastolic_bp: int = Field(..., ge=40, le=160, description="Diastolic BP (mmHg)")
    total_cholesterol: int = Field(..., ge=80, le=600, description="Serum cholesterol in mg/dL")
    fasting_blood_sugar: float = Field(..., ge=50, le=500, description="Fasting blood glucose in mg/dL")
    resting_ecg: int = Field(0, ge=0, le=2, description="0: Normal, 1: ST-T wave abnorm, 2: LVH")
    max_heart_rate: int = Field(..., ge=50, le=240, description="Maximum heart rate achieved (bpm)")

    # Lifestyle
    smoker: bool = Field(False, description="Current or recent smoker")
    physical_activity: bool = Field(True, description="Regular exercise / physical activity")
    fruits_diet: bool = Field(True, description="Consumes fruit >= 1 per day")
    veggies_diet: bool = Field(True, description="Consumes vegetables >= 1 per day")
    heavy_alcohol: bool = Field(False, description="Heavy alcohol consumption")

    # Symptoms & Clinical History
    chest_pain_type: int = Field(0, ge=0, le=3, description="0: Typical Angina, 1: Atypical, 2: Non-anginal, 3: Asymptomatic")
    exercise_angina: bool = Field(False, description="Exercise-induced angina")
    st_depression: float = Field(0.0, ge=0.0, le=10.0, description="ST depression (oldpeak)")
    st_slope: int = Field(1, ge=0, le=2, description="ST segment slope (0: Up, 1: Flat, 2: Down)")
    major_vessels: int = Field(0, ge=0, le=3, description="Number of major vessels (0-3)")
    general_health: int = Field(2, ge=1, le=5, description="1: Excellent to 5: Poor")
    physical_health_days: int = Field(0, ge=0, le=30, description="Unhealthy physical days in past 30 days")
    mental_health_days: int = Field(0, ge=0, le=30, description="Unhealthy mental days in past 30 days")
    diff_walking: bool = Field(False, description="Difficulty walking or climbing stairs")
    stroke_history: bool = Field(False, description="Prior diagnosis of stroke")
    heart_disease_history: bool = Field(False, description="Prior heart attack / coronary disease")

    additional_notes: Optional[str] = None

class SurveyCreate(SurveyBase):
    pass

class SurveyOut(SurveyBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
