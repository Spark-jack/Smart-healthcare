import pytest
from app.services.ml_engine import ml_engine

def test_ml_engine_models_loaded_and_calibrated():
    assert ml_engine.diabetes_model is not None, "Diabetes calibrated model should be loaded"
    assert ml_engine.heart_model is not None, "Cardiovascular calibrated model should be loaded"
    assert ml_engine.diabetes_meta is not None
    assert ml_engine.heart_meta is not None
    assert "expected_calibration_error" in ml_engine.diabetes_meta
    assert "expected_calibration_error" in ml_engine.heart_meta
    assert ml_engine.diabetes_meta.get("data_source") == "real"
    assert ml_engine.heart_meta.get("data_source") == "real"

def test_data_quality_check():
    # Full valid data
    full_data = {
        "systolic_bp": 125,
        "total_cholesterol": 190,
        "fasting_blood_sugar": 92,
        "st_depression": 0.0,
        "max_heart_rate": 150,
        "height_cm": 175.0,
        "weight_kg": 72.0,
        "age": 45,
        "general_health": 2
    }
    is_valid, warn_text = ml_engine.check_data_quality(full_data)
    assert is_valid is True
    assert warn_text is None

    # Missing systolic_bp and total_cholesterol
    partial_data = {
        "fasting_blood_sugar": 95
    }
    is_valid_part, warn_text_part = ml_engine.check_data_quality(partial_data)
    assert is_valid_part is False
    assert "systolic BP" in warn_text_part
    assert "total cholesterol" in warn_text_part

def test_diabetes_prediction_calibration_and_uncertainty():
    survey_data = {
        "high_bp": True,
        "high_chol": True,
        "chol_check": True,
        "bmi": 32.5,
        "smoker": False,
        "stroke_history": False,
        "heart_disease_history": False,
        "phys_activity": True,
        "fruits": True,
        "veggies": True,
        "heavy_alcohol": False,
        "gen_health": 3,
        "mental_health_days": 2,
        "physical_health_days": 4,
        "diff_walk": False,
        "gender": "Male",
        "age": 55,
        "systolic_bp": 135,
        "total_cholesterol": 210,
        "fasting_blood_sugar": 105,
        "max_heart_rate": 140,
        "st_depression": 0.0,
        "height_cm": 178.0,
        "weight_kg": 85.0,
        "general_health": 3
    }

    result = ml_engine.predict_diabetes(survey_data)
    score, category, confidence, df = result

    # Check calibrated score bounds
    assert 0.0 <= score <= 100.0
    assert category in ["Low", "Medium", "High"]
    assert 0.0 <= confidence <= 1.0

    # Principled uncertainty interval
    assert hasattr(result, "uncertainty_interval")
    low, high = result.uncertainty_interval
    assert 0.0 <= low <= score <= high <= 100.0

    # Data source metadata
    assert result.data_source == "real"
    assert result.ece is not None

def test_heart_prediction_calibration_and_uncertainty():
    survey_data = {
        "age": 62,
        "gender": "Male",
        "chest_pain_type": 0,
        "systolic_bp": 150,
        "total_cholesterol": 240,
        "fasting_blood_sugar": 125,
        "resting_ecg": 1,
        "max_heart_rate": 130,
        "exercise_angina": True,
        "st_depression": 2.2,
        "st_slope": 1,
        "major_vessels": 2,
        "thalassemia": 2,
        "height_cm": 175.0,
        "weight_kg": 80.0,
        "general_health": 4
    }

    result = ml_engine.predict_heart(survey_data)
    score, category, confidence, df = result

    assert 0.0 <= score <= 100.0
    assert category in ["Low", "Medium", "High"]
    assert hasattr(result, "uncertainty_interval")
    low, high = result.uncertainty_interval
    assert 0.0 <= low <= score <= high <= 100.0
    assert result.data_source == "real"
