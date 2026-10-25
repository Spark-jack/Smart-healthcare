import pytest
from app.services.triage_engine import triage_engine

def test_triage_hypertensive_crisis_triggers():
    # Systolic >= 180
    score, level, breakdown, timeframe = triage_engine.calculate_urgency(
        diabetes_risk=10.0,
        cardio_risk=10.0,
        survey_data={"systolic_bp": 185, "diastolic_bp": 85}
    )
    assert any("Hypertensive Crisis" in t for t in breakdown["acute_symptom_triggers"])
    assert breakdown["total_symptom_addition"] >= 28.0

    # Diastolic >= 120
    score_d, level_d, breakdown_d, _ = triage_engine.calculate_urgency(
        diabetes_risk=10.0,
        cardio_risk=10.0,
        survey_data={"systolic_bp": 130, "diastolic_bp": 125}
    )
    assert any("Hypertensive Crisis" in t for t in breakdown_d["acute_symptom_triggers"])

def test_triage_angina_triggers():
    # Typical chest pain (type 0)
    score, _, breakdown, _ = triage_engine.calculate_urgency(
        diabetes_risk=5.0,
        cardio_risk=5.0,
        survey_data={"chest_pain_type": 0, "exercise_angina": False}
    )
    assert any("Typical or exertional chest pain" in t for t in breakdown["acute_symptom_triggers"])

    # Atypical with exercise angina (type 1 + exang)
    score_ex, _, breakdown_ex, _ = triage_engine.calculate_urgency(
        diabetes_risk=5.0,
        cardio_risk=5.0,
        survey_data={"chest_pain_type": 1, "exercise_angina": True}
    )
    assert any("Typical or exertional chest pain" in t for t in breakdown_ex["acute_symptom_triggers"])

def test_triage_st_depression_thresholds():
    # Significant ST depression >= 2.0 mm
    score_sig, _, breakdown_sig, _ = triage_engine.calculate_urgency(
        diabetes_risk=0.0,
        cardio_risk=0.0,
        survey_data={"st_depression": 2.5}
    )
    assert any("Significant ST segment depression (2.5 mm)" in t for t in breakdown_sig["acute_symptom_triggers"])
    assert breakdown_sig["total_symptom_addition"] == 16.0

    # Moderate ST depression >= 1.0 mm
    score_mod, _, breakdown_mod, _ = triage_engine.calculate_urgency(
        diabetes_risk=0.0,
        cardio_risk=0.0,
        survey_data={"st_depression": 1.4}
    )
    assert any("Moderate ST depression (1.4 mm)" in t for t in breakdown_mod["acute_symptom_triggers"])
    assert breakdown_mod["total_symptom_addition"] == 8.0

def test_triage_stroke_and_prior_mi_triggers():
    score, _, breakdown, _ = triage_engine.calculate_urgency(
        diabetes_risk=0.0,
        cardio_risk=0.0,
        survey_data={"stroke_history": True, "heart_disease_history": True}
    )
    assert any("stroke" in t.lower() for t in breakdown["acute_symptom_triggers"])
    assert any("heart attack" in t.lower() or "coronary" in t.lower() for t in breakdown["acute_symptom_triggers"])
    assert breakdown["total_symptom_addition"] == 24.0

def test_triage_hyperglycemia_triggers():
    # Severe >= 250 mg/dL
    _, _, breakdown_sev, _ = triage_engine.calculate_urgency(
        diabetes_risk=0.0,
        cardio_risk=0.0,
        survey_data={"fasting_blood_sugar": 280}
    )
    assert any("Severe hyperglycemia" in t for t in breakdown_sev["acute_symptom_triggers"])

    # Moderate >= 180 mg/dL
    _, _, breakdown_mod, _ = triage_engine.calculate_urgency(
        diabetes_risk=0.0,
        cardio_risk=0.0,
        survey_data={"fasting_blood_sugar": 195}
    )
    assert any("Elevated fasting glucose" in t for t in breakdown_mod["acute_symptom_triggers"])

def test_triage_urgency_tier_boundaries():
    # 1. Routine tier (< 35)
    score_routine, level_routine, _, _ = triage_engine.calculate_urgency(
        diabetes_risk=20.0,
        cardio_risk=20.0,
        survey_data={} # baseline = 20 * 0.45 = 9.0
    )
    assert score_routine < 35.0
    assert level_routine == "Routine"

    # 2. Moderate tier (35.0 to 59.9)
    # base_risk = 80 * 0.45 = 36.0
    score_mod, level_mod, _, _ = triage_engine.calculate_urgency(
        diabetes_risk=80.0,
        cardio_risk=50.0,
        survey_data={}
    )
    assert 35.0 <= score_mod < 60.0
    assert level_mod == "Moderate"

    # Exact boundary 35.0 test
    # base_risk = 35 / 0.45 = 77.777
    score_35, level_35, _, _ = triage_engine.calculate_urgency(
        diabetes_risk=77.8,
        cardio_risk=0.0,
        survey_data={}
    )
    assert score_35 == 35.0
    assert level_35 == "Moderate"

    # 3. High tier (60.0 to 79.9)
    # base_risk = 90 * 0.45 = 40.5 + 24.0 (stroke + heart) = 64.5
    score_high, level_high, _, _ = triage_engine.calculate_urgency(
        diabetes_risk=90.0,
        cardio_risk=90.0,
        survey_data={"stroke_history": True, "heart_disease_history": True}
    )
    assert 60.0 <= score_high < 80.0
    assert level_high == "High"

    # Exact boundary 60.0 test
    # base_risk = 80 * 0.45 = 36.0 + 24.0 (stroke + heart attack) = 60.0
    score_60, level_60, _, _ = triage_engine.calculate_urgency(
        diabetes_risk=80.0,
        cardio_risk=0.0,
        survey_data={"stroke_history": True, "heart_disease_history": True}
    )
    assert score_60 == 60.0
    assert level_60 == "High"

    # 4. Critical tier (>= 80.0)
    # base_risk = 90 * 0.45 = 40.5 + 28 (crisis BP) + 18 (angina) = 86.5
    score_crit, level_crit, _, timeframe = triage_engine.calculate_urgency(
        diabetes_risk=90.0,
        cardio_risk=90.0,
        survey_data={"systolic_bp": 185, "chest_pain_type": 0}
    )
    assert score_crit >= 80.0
    assert level_crit == "Critical"
    assert "Immediate / Within 24 Hours" in timeframe
