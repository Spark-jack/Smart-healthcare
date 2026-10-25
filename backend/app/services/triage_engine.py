from typing import Dict, Any

class TriageEngine:
    @staticmethod
    def calculate_urgency(
        diabetes_risk: float,
        cardio_risk: float,
        survey_data: dict
    ) -> tuple[float, str, dict, str]:
        """
        Calculates Urgency Score (0-100), Priority Level, Factor Breakdown, and Recommended Clinical Timeframe.
        """
        # Baseline urgency anchors from the higher predicted disease risk
        base_risk = max(diabetes_risk, cardio_risk) * 0.45 # 0 to 45 points

        symptom_points = 0.0
        breakdown = {
            "baseline_ml_risk_contribution": round(base_risk, 1),
            "acute_symptom_triggers": []
        }

        # 1. Acute Blood Pressure evaluation
        systolic = survey_data.get("systolic_bp", 120)
        diastolic = survey_data.get("diastolic_bp", 80)
        if systolic >= 180 or diastolic >= 120:
            symptom_points += 28.0
            breakdown["acute_symptom_triggers"].append("Hypertensive Crisis range BP (systolic >= 180 or diastolic >= 120)")
        elif systolic >= 160 or diastolic >= 100:
            symptom_points += 16.0
            breakdown["acute_symptom_triggers"].append("Stage 2 Hypertension (systolic >= 160)")

        # 2. Angina & Ischemia signs
        chest_pain = survey_data.get("chest_pain_type", 3)
        exang = survey_data.get("exercise_angina", False)
        oldpeak = float(survey_data.get("st_depression", 0.0))

        if chest_pain == 0 or (chest_pain == 1 and exang): # Typical angina or exertional
            symptom_points += 18.0
            breakdown["acute_symptom_triggers"].append("Typical or exertional chest pain reported")

        if oldpeak >= 2.0:
            symptom_points += 16.0
            breakdown["acute_symptom_triggers"].append(f"Significant ST segment depression ({oldpeak} mm)")
        elif oldpeak >= 1.0:
            symptom_points += 8.0
            breakdown["acute_symptom_triggers"].append(f"Moderate ST depression ({oldpeak} mm)")

        # 3. Critical history (prior stroke or myocardial infarction)
        stroke = survey_data.get("stroke_history", False)
        heart_attack = survey_data.get("heart_disease_history", False)
        if stroke:
            symptom_points += 12.0
            breakdown["acute_symptom_triggers"].append("Documented history of cerebrovascular stroke")
        if heart_attack:
            symptom_points += 12.0
            breakdown["acute_symptom_triggers"].append("Documented prior coronary event / heart attack")

        # 4. Metabolic decompensation (Severe fasting glucose)
        fbs = survey_data.get("fasting_blood_sugar", 95)
        if fbs >= 250:
            symptom_points += 16.0
            breakdown["acute_symptom_triggers"].append(f"Severe hyperglycemia (Fasting glucose {fbs} mg/dL)")
        elif fbs >= 180:
            symptom_points += 8.0
            breakdown["acute_symptom_triggers"].append(f"Elevated fasting glucose ({fbs} mg/dL)")

        total_score = min(100.0, round(base_risk + symptom_points, 1))
        breakdown["total_symptom_addition"] = round(symptom_points, 1)

        # Categorize
        if total_score >= 80.0:
            urgency_level = "Critical"
            timeframe = "Immediate / Within 24 Hours (Urgent Care / Emergency evaluation if acute chest pain occurs)"
        elif total_score >= 60.0:
            urgency_level = "High"
            timeframe = "Priority Specialist Consult within 48 to 72 Hours"
        elif total_score >= 35.0:
            urgency_level = "Moderate"
            timeframe = "Clinical Review & Diagnostics within 1 to 2 Weeks"
        else:
            urgency_level = "Routine"
            timeframe = "Elective Health Check & Preventive Guidance within 3 to 4 Weeks"

        return total_score, urgency_level, breakdown, timeframe

triage_engine = TriageEngine()
