import os
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from app.core.config import settings

MODELS_DIR = settings.MODELS_DIR

class ShapExplainerService:
    def __init__(self):
        self.diabetes_explainer = None
        self.heart_explainer = None
        self.diabetes_meta = None
        self.heart_meta = None
        self._load_explainers()

    def _load_explainers(self):
        d_exp_path = os.path.join(MODELS_DIR, "diabetes_explainer.joblib")
        h_exp_path = os.path.join(MODELS_DIR, "heart_explainer.joblib")
        d_meta_path = os.path.join(MODELS_DIR, "diabetes_metadata.json")
        h_meta_path = os.path.join(MODELS_DIR, "heart_metadata.json")

        if os.path.exists(d_exp_path) and os.path.exists(d_meta_path):
            self.diabetes_explainer = joblib.load(d_exp_path)
            with open(d_meta_path, "r") as f:
                self.diabetes_meta = json.load(f)

        if os.path.exists(h_exp_path) and os.path.exists(h_meta_path):
            self.heart_explainer = joblib.load(h_exp_path)
            with open(h_meta_path, "r") as f:
                self.heart_meta = json.load(f)

    def _format_factor_interpretation(self, feature: str, val: Any, impact: str, shap_val: float, disease: str) -> str:
        pct = abs(round(shap_val * 100, 1))
        direction = "increases" if impact == "increases_risk" else "mitigates / lowers"

        interpretations = {
            "HighBP": f"High Blood Pressure ({val}) {direction} metabolic stress by {pct}%.",
            "HighChol": f"High Cholesterol reading ({val}) {direction} arterial plaque risk by {pct}%.",
            "BMI": f"Body Mass Index of {val} {direction} estimated {disease.lower()} probability by {pct}%.",
            "Smoker": f"Smoking history ({val}) {direction} systemic vascular risk by {pct}%.",
            "Stroke": f"Past stroke event {direction} risk profile by {pct}%.",
            "PhysActivity": f"Physical exercise habits {direction} metabolic risk by {pct}%.",
            "Fruits": f"Fruit dietary intake {direction} oxidative stress indicators by {pct}%.",
            "Veggies": f"Vegetable dietary intake {direction} metabolic strain by {pct}%.",
            "GenHlth": f"General health perception rating ({val}/5) {direction} calculated risk by {pct}%.",
            "Age": f"Patient age ({val} yrs) baseline contribution: {pct}% {direction}.",
            "age": f"Age ({val} yrs) clinical vulnerability index: {pct}% {direction}.",
            "trestbps": f"Resting systolic blood pressure ({val} mmHg) {direction} cardiac workload by {pct}%.",
            "chol": f"Serum cholesterol ({val} mg/dL) {direction} atherosclerotic burden by {pct}%.",
            "thalach": f"Peak heart rate reached ({val} bpm) {direction} coronary reserve risk by {pct}%.",
            "exang": f"Exercise-induced angina symptom ({val}) {direction} myocardial ischemia risk by {pct}%.",
            "oldpeak": f"ST segment depression ({val} mm) {direction} ischemic event likelihood by {pct}%.",
            "ca": f"Number of major fluoroscopy vessels ({val}) {direction} coronary risk by {pct}%.",
            "cp": f"Chest pain profile type ({val}) {direction} cardiac risk urgency by {pct}%.",
        }

        return interpretations.get(
            feature,
            f"{feature} (value: {val}) {direction} {disease} risk score by {pct}%."
        )

    def explain_prediction(self, explainer, meta: dict, input_df: pd.DataFrame, disease_name: str, top_k: int = 5) -> tuple[float, List[Dict[str, Any]], str]:
        if explainer is None:
            self._load_explainers()

        shap_values = explainer.shap_values(input_df)
        # Handle binary classification shapes
        if isinstance(shap_values, list) and len(shap_values) > 1:
            # Positive class SHAP
            shap_vector = shap_values[1][0]
        elif len(np.shape(shap_values)) == 2:
            shap_vector = shap_values[0]
        else:
            shap_vector = shap_values

        base_value = float(meta.get("base_value", 0.0))
        features = meta.get("feature_cols", list(input_df.columns))
        friendly_names = meta.get("feature_friendly_names", {})

        factors = []
        for feat, val, s_val in zip(features, input_df.iloc[0], shap_vector):
            impact = "increases_risk" if s_val > 0 else "decreases_risk"
            factors.append({
                "feature": feat,
                "feature_label": friendly_names.get(feat, feat),
                "shap_value": round(float(s_val), 4),
                "feature_value": float(val) if isinstance(val, (int, float, np.number)) else str(val),
                "impact": impact,
                "abs_importance": abs(float(s_val)),
                "interpretation": self._format_factor_interpretation(feat, val, impact, float(s_val), disease_name)
            })

        # Sort by absolute SHAP value magnitude
        factors.sort(key=lambda x: x["abs_importance"], reverse=True)
        top_factors = factors[:top_k]

        # Clean out temporary key
        for item in top_factors:
            item.pop("abs_importance", None)

        # Generate clinician summary insight
        pos_drivers = [f["feature_label"] for f in top_factors if f["impact"] == "increases_risk"]
        neg_drivers = [f["feature_label"] for f in top_factors if f["impact"] == "decreases_risk"]

        if pos_drivers:
            summary = f"Primary clinical risk accelerators: {', '.join(pos_drivers[:2])}."
            if neg_drivers:
                summary += f" Protective factors include: {', '.join(neg_drivers[:2])}."
        else:
            summary = "Patient presents strong baseline protective factors with minimal disease drivers."

        return base_value, top_factors, summary

    def explain_diabetes(self, input_df: pd.DataFrame):
        return self.explain_prediction(
            self.diabetes_explainer, self.diabetes_meta, input_df, "Diabetes"
        )

    def explain_heart(self, input_df: pd.DataFrame):
        return self.explain_prediction(
            self.heart_explainer, self.heart_meta, input_df, "Cardiovascular Disease"
        )

shap_service = ShapExplainerService()
