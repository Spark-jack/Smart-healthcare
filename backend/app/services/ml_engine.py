import os
import json
from typing import Optional, List, Tuple, Dict, Any
import joblib
import numpy as np
import pandas as pd
from app.core.config import settings

MODELS_DIR = settings.MODELS_DIR

class PredictionOutput(tuple):
    """
    Backwards-compatible tuple (score, category, confidence, df) that also exposes
    principled uncertainty_interval, data_quality_warning, data_source, and ece.
    """
    def __new__(cls, score, category, confidence, df, uncertainty_interval, data_quality_warning, data_source, ece):
        return super().__new__(cls, (score, category, confidence, df))

    def __init__(self, score, category, confidence, df, uncertainty_interval, data_quality_warning, data_source, ece):
        self.score = score
        self.category = category
        self.confidence = confidence
        self.df = df
        self.uncertainty_interval = uncertainty_interval
        self.data_quality_warning = data_quality_warning
        self.data_source = data_source
        self.ece = ece

class MLEngine:
    def __init__(self):
        self.diabetes_model = None
        self.heart_model = None
        self.diabetes_meta = None
        self.heart_meta = None
        self._load_models()

    def _load_models(self):
        diabetes_model_path = os.path.join(MODELS_DIR, "diabetes_model.joblib")
        heart_model_path = os.path.join(MODELS_DIR, "heart_model.joblib")
        diabetes_meta_path = os.path.join(MODELS_DIR, "diabetes_metadata.json")
        heart_meta_path = os.path.join(MODELS_DIR, "heart_metadata.json")

        if os.path.exists(diabetes_model_path) and os.path.exists(diabetes_meta_path):
            self.diabetes_model = joblib.load(diabetes_model_path)
            with open(diabetes_meta_path, "r") as f:
                self.diabetes_meta = json.load(f)

        if os.path.exists(heart_model_path) and os.path.exists(heart_meta_path):
            self.heart_model = joblib.load(heart_model_path)
            with open(heart_meta_path, "r") as f:
                self.heart_meta = json.load(f)

    def check_data_quality(self, survey_data: dict) -> tuple[bool, Optional[str]]:
        """
        Validates clinical survey completeness. Adds a warning if essential fields were omitted or defaulted.
        """
        missing = []
        if survey_data.get("systolic_bp") is None:
            missing.append("systolic BP")
        if survey_data.get("total_cholesterol") is None:
            missing.append("total cholesterol")
        if survey_data.get("height_cm") is None or survey_data.get("weight_kg") is None:
            missing.append("height/weight biometrics")
        if survey_data.get("age") is None:
            missing.append("patient age")
        if survey_data.get("general_health") is None:
            missing.append("general health self-rating")

        if missing:
            warning = f"Low data quality warning: Critical survey telemetry omitted ({', '.join(missing)}). Population standard defaults were imputed, widening uncertainty intervals."
            return False, warning
        return True, None

    def _calculate_uncertainty(self, proba: float, meta: dict, is_low_quality: bool) -> tuple[float, list[float]]:
        """
        Computes a principled 95% uncertainty interval and calibrated confidence score based on ECE and standard error.
        """
        ece = float(meta.get("expected_calibration_error", 0.05)) if meta else 0.05
        # Binomial SE around calibrated predicted probability + ECE
        sample_size_factor = 50.0 if is_low_quality else 100.0
        se = np.sqrt(max(0.005, proba * (1.0 - proba)) / sample_size_factor) + ece
        if is_low_quality:
            se *= 1.30

        margin = 1.96 * se
        low = round(max(0.0, (proba - margin)) * 100, 1)
        high = round(min(100.0, (proba + margin)) * 100, 1)
        interval = [low, high]

        # Principled confidence measure: bounded between 0.40 and 0.99 reflecting calibration certainty
        interval_width = (high - low) / 100.0
        confidence = round(float(max(0.40, min(0.99, 1.0 - (interval_width * 0.7 + ece * 0.3)))), 3)
        return confidence, interval

    def extract_diabetes_df(self, survey_data: dict) -> pd.DataFrame:
        """Converts incoming survey data to exact Diabetes model feature schema."""
        systolic = survey_data.get("systolic_bp", 120)
        chol = survey_data.get("total_cholesterol", 190)
        gender_str = str(survey_data.get("gender", "Female")).lower()
        sex_binary = 1 if "male" in gender_str and "female" not in gender_str else 0

        # Calculate BMI if needed
        height_m = survey_data.get("height_cm", 170) / 100.0
        weight_kg = survey_data.get("weight_kg", 70)
        bmi = survey_data.get("bmi") or round(weight_kg / (height_m ** 2), 1)

        row = {
            "HighBP": 1 if systolic >= 135 else 0,
            "HighChol": 1 if chol >= 200 else 0,
            "CholCheck": 1,
            "BMI": float(bmi),
            "Smoker": 1 if survey_data.get("smoker", False) else 0,
            "Stroke": 1 if survey_data.get("stroke_history", False) else 0,
            "HeartDiseaseorAttack": 1 if survey_data.get("heart_disease_history", False) else 0,
            "PhysActivity": 1 if survey_data.get("physical_activity", True) else 0,
            "Fruits": 1 if survey_data.get("fruits_diet", True) else 0,
            "Veggies": 1 if survey_data.get("veggies_diet", True) else 0,
            "HvyAlcoholConsump": 1 if survey_data.get("heavy_alcohol", False) else 0,
            "GenHlth": int(survey_data.get("general_health", 2)),
            "MentHlth": int(survey_data.get("mental_health_days", 0)),
            "PhysHlth": int(survey_data.get("physical_health_days", 0)),
            "DiffWalk": 1 if survey_data.get("diff_walking", False) else 0,
            "Sex": sex_binary,
            "Age": int(survey_data.get("age", 45))
        }
        cols = self.diabetes_meta["feature_cols"] if self.diabetes_meta else list(row.keys())
        return pd.DataFrame([row])[cols]

    def extract_heart_df(self, survey_data: dict) -> pd.DataFrame:
        """Converts incoming survey data to exact UCI Heart Disease feature schema."""
        gender_str = str(survey_data.get("gender", "Male")).lower()
        sex_binary = 1 if "male" in gender_str and "female" not in gender_str else 0
        fbs_val = 1 if survey_data.get("fasting_blood_sugar", 100) > 120 else 0

        row = {
            "age": int(survey_data.get("age", 50)),
            "sex": sex_binary,
            "cp": int(survey_data.get("chest_pain_type", 0)),
            "trestbps": int(survey_data.get("systolic_bp", 125)),
            "chol": int(survey_data.get("total_cholesterol", 200)),
            "fbs": fbs_val,
            "restecg": int(survey_data.get("resting_ecg", 0)),
            "thalach": int(survey_data.get("max_heart_rate", 145)),
            "exang": 1 if survey_data.get("exercise_angina", False) else 0,
            "oldpeak": float(survey_data.get("st_depression", 0.0)),
            "slope": int(survey_data.get("st_slope", 1)),
            "ca": int(survey_data.get("major_vessels", 0))
        }
        cols = self.heart_meta["feature_cols"] if self.heart_meta else list(row.keys())
        return pd.DataFrame([row])[cols]

    def predict_diabetes(self, survey_dict: dict) -> PredictionOutput:
        if self.diabetes_model is None:
            self._load_models()
        df = self.extract_diabetes_df(survey_dict)
        proba = float(self.diabetes_model.predict_proba(df)[0, 1])
        score = round(proba * 100, 1)

        if score < 30.0:
            category = "Low"
        elif score < 65.0:
            category = "Medium"
        else:
            category = "High"

        is_good_qual, warning = self.check_data_quality(survey_dict)
        confidence, interval = self._calculate_uncertainty(proba, self.diabetes_meta, not is_good_qual)
        data_source = self.diabetes_meta.get("data_source", "real") if self.diabetes_meta else "real"
        ece = self.diabetes_meta.get("expected_calibration_error", 0.0038) if self.diabetes_meta else 0.0038

        return PredictionOutput(
            score=score,
            category=category,
            confidence=confidence,
            df=df,
            uncertainty_interval=interval,
            data_quality_warning=warning,
            data_source=data_source,
            ece=ece
        )

    def predict_heart(self, survey_dict: dict) -> PredictionOutput:
        if self.heart_model is None:
            self._load_models()
        df = self.extract_heart_df(survey_dict)
        proba = float(self.heart_model.predict_proba(df)[0, 1])
        score = round(proba * 100, 1)

        if score < 30.0:
            category = "Low"
        elif score < 65.0:
            category = "Medium"
        else:
            category = "High"

        is_good_qual, warning = self.check_data_quality(survey_dict)
        confidence, interval = self._calculate_uncertainty(proba, self.heart_meta, not is_good_qual)
        data_source = self.heart_meta.get("data_source", "real") if self.heart_meta else "real"
        ece = self.heart_meta.get("expected_calibration_error", 0.1106) if self.heart_meta else 0.1106

        return PredictionOutput(
            score=score,
            category=category,
            confidence=confidence,
            df=df,
            uncertainty_interval=interval,
            data_quality_warning=warning,
            data_source=data_source,
            ece=ece
        )

ml_engine = MLEngine()
