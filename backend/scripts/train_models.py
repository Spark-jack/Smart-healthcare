import os
import json
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    roc_auc_score, accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, brier_score_loss
)
from xgboost import XGBClassifier
import shap

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def compute_ece(y_true, y_prob, n_bins=10):
    """Computes Expected Calibration Error (ECE)."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.digitize(y_prob, bins) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    
    ece = 0.0
    n = len(y_prob)
    y_true_arr = np.array(y_true)
    for b in range(n_bins):
        mask = bin_indices == b
        count = np.sum(mask)
        if count > 0:
            avg_pred = np.mean(y_prob[mask])
            avg_true = np.mean(y_true_arr[mask])
            ece += (count / n) * abs(avg_pred - avg_true)
    return float(ece)

def train_diabetes_model():
    print("=" * 60)
    print("Training Calibrated Diabetes Risk Model (XGBoost + CalibratedClassifierCV)...")
    data_path = os.path.join(DATA_DIR, "diabetes_data.csv")
    info_path = os.path.join(DATA_DIR, "diabetes_info.json")
    
    source_info = {}
    if os.path.exists(info_path):
        with open(info_path, "r") as f:
            source_info = json.load(f)
    else:
        source_info = {
            "data_source": "real",
            "dataset_name": "CDC BRFSS 2015 Diabetes Health Indicators",
            "source_url": "https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators",
            "row_count": 0
        }

    df = pd.read_csv(data_path)
    source_info["row_count"] = len(df)

    feature_cols = [
        "HighBP", "HighChol", "CholCheck", "BMI", "Smoker", "Stroke",
        "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
        "HvyAlcoholConsump", "GenHlth", "MentHlth", "PhysHlth", "DiffWalk",
        "Sex", "Age"
    ]
    X = df[feature_cols]
    y = df["Diabetes_binary"].astype(int)

    # Stratified split: 80% train+val, 20% held-out test
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    # Split train+val into 75% train, 25% val (yielding 60% train, 20% val, 20% test overall)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full
    )

    base_model = XGBClassifier(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="logloss"
    )
    base_model.fit(X_train, y_train)

    try:
        from sklearn.frozen import FrozenEstimator
        cal_iso = CalibratedClassifierCV(FrozenEstimator(base_model), method="isotonic")
        cal_sig = CalibratedClassifierCV(FrozenEstimator(base_model), method="sigmoid")
    except (ImportError, TypeError):
        cal_iso = CalibratedClassifierCV(estimator=base_model, method="isotonic", cv="prefit")
        cal_sig = CalibratedClassifierCV(estimator=base_model, method="sigmoid", cv="prefit")

    cal_iso.fit(X_val, y_val)
    brier_iso = brier_score_loss(y_val, cal_iso.predict_proba(X_val)[:, 1])

    cal_sig.fit(X_val, y_val)
    brier_sig = brier_score_loss(y_val, cal_sig.predict_proba(X_val)[:, 1])

    if brier_iso <= brier_sig:
        calibrated_model = cal_iso
        best_cal_method = "isotonic"
        best_val_brier = brier_iso
    else:
        calibrated_model = cal_sig
        best_cal_method = "sigmoid"
        best_val_brier = brier_sig

    print(f"Calibration Method Selected: {best_cal_method} (Val Brier: {best_val_brier:.4f})")

    # Evaluate strictly on held-out test set
    y_test_proba = calibrated_model.predict_proba(X_test)[:, 1]
    y_test_pred = (y_test_proba >= 0.5).astype(int)

    test_auc = roc_auc_score(y_test, y_test_proba)
    test_acc = accuracy_score(y_test, y_test_pred)
    test_prec = precision_score(y_test, y_test_pred, zero_division=0)
    test_rec = recall_score(y_test, y_test_pred, zero_division=0)
    test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
    test_cm = confusion_matrix(y_test, y_test_pred).tolist()
    test_brier = brier_score_loss(y_test, y_test_proba)
    test_ece = compute_ece(y_test, y_test_proba, n_bins=10)

    # Reliability diagram
    prob_true, prob_pred = calibration_curve(y_test, y_test_proba, n_bins=10, strategy="uniform")
    reliability_diagram = [
        {"bin_pred": round(float(p), 4), "observed_rate": round(float(t), 4)}
        for p, t in zip(prob_pred, prob_true)
    ]

    print(f"Held-Out Test Results -> AUC: {test_auc:.4f}, Acc: {test_acc:.4f}, ECE: {test_ece:.4f}, Brier: {test_brier:.4f}")

    # Build SHAP TreeExplainer from the base tree model
    explainer = shap.TreeExplainer(base_model)
    base_val = explainer.expected_value
    if isinstance(base_val, (list, np.ndarray)):
        base_val = float(base_val[1] if len(base_val) > 1 else base_val[0])
    else:
        base_val = float(base_val)

    # Save artifacts
    model_path = os.path.join(MODELS_DIR, "diabetes_model.joblib")
    explainer_path = os.path.join(MODELS_DIR, "diabetes_explainer.joblib")
    meta_path = os.path.join(MODELS_DIR, "diabetes_metadata.json")

    joblib.dump(calibrated_model, model_path)
    joblib.dump(explainer, explainer_path)

    metadata = {
        "disease": "Diabetes",
        "data_source": source_info.get("data_source", "real"),
        "dataset_name": source_info.get("dataset_name", "CDC BRFSS 2015 Diabetes Health Indicators"),
        "source_url": source_info.get("source_url", "https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators"),
        "row_count": int(source_info.get("row_count", len(df))),
        "date_trained": datetime.now(timezone.utc).isoformat(),
        "feature_cols": feature_cols,
        "calibration_method": best_cal_method,
        "auc_roc": round(float(test_auc), 4),
        "accuracy": round(float(test_acc), 4),
        "precision": round(float(test_prec), 4),
        "recall": round(float(test_rec), 4),
        "f1_score": round(float(test_f1), 4),
        "confusion_matrix": test_cm,
        "brier_score": round(float(test_brier), 4),
        "expected_calibration_error": round(float(test_ece), 4),
        "reliability_diagram": reliability_diagram,
        "base_value": round(base_val, 4),
        "feature_friendly_names": {
            "HighBP": "High Blood Pressure",
            "HighChol": "High Cholesterol",
            "CholCheck": "Recent Cholesterol Screening",
            "BMI": "Body Mass Index (BMI)",
            "Smoker": "Smoking Status",
            "Stroke": "Stroke History",
            "HeartDiseaseorAttack": "Coronary Heart History",
            "PhysActivity": "Physical Exercise Level",
            "Fruits": "Daily Fruit Intake",
            "Veggies": "Daily Vegetable Intake",
            "HvyAlcoholConsump": "Heavy Alcohol Consumption",
            "GenHlth": "General Health Self-Rating",
            "MentHlth": "Poor Mental Health Days",
            "PhysHlth": "Poor Physical Health Days",
            "DiffWalk": "Difficulty Walking / Mobility",
            "Sex": "Biological Sex",
            "Age": "Patient Age"
        }
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Saved calibrated diabetes model & metadata to {MODELS_DIR}")
    return metadata

def train_heart_model():
    print("=" * 60)
    print("Training Calibrated Cardiovascular Model (XGBoost + CalibratedClassifierCV)...")
    data_path = os.path.join(DATA_DIR, "heart_disease.csv")
    info_path = os.path.join(DATA_DIR, "heart_info.json")

    source_info = {}
    if os.path.exists(info_path):
        with open(info_path, "r") as f:
            source_info = json.load(f)
    else:
        source_info = {
            "data_source": "real",
            "dataset_name": "UCI Cleveland Clinic Heart Disease",
            "source_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data",
            "row_count": 0
        }

    df = pd.read_csv(data_path)
    source_info["row_count"] = len(df)

    feature_cols = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", 
        "restecg", "thalach", "exang", "oldpeak", "slope", "ca"
    ]
    X = df[feature_cols]
    y = df["target"].astype(int)

    # Stratified split: 80% train+val, 20% test
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    # Split train+val into 75% train, 25% val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.25, random_state=42, stratify=y_train_full
    )

    base_model = XGBClassifier(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42,
        eval_metric="logloss"
    )
    base_model.fit(X_train, y_train)

    # Calibration comparison
    try:
        from sklearn.frozen import FrozenEstimator
        cal_iso = CalibratedClassifierCV(FrozenEstimator(base_model), method="isotonic")
        cal_sig = CalibratedClassifierCV(FrozenEstimator(base_model), method="sigmoid")
    except (ImportError, TypeError):
        cal_iso = CalibratedClassifierCV(estimator=base_model, method="isotonic", cv="prefit")
        cal_sig = CalibratedClassifierCV(estimator=base_model, method="sigmoid", cv="prefit")

    cal_iso.fit(X_val, y_val)
    brier_iso = brier_score_loss(y_val, cal_iso.predict_proba(X_val)[:, 1])

    cal_sig.fit(X_val, y_val)
    brier_sig = brier_score_loss(y_val, cal_sig.predict_proba(X_val)[:, 1])

    if brier_iso <= brier_sig:
        calibrated_model = cal_iso
        best_cal_method = "isotonic"
        best_val_brier = brier_iso
    else:
        calibrated_model = cal_sig
        best_cal_method = "sigmoid"
        best_val_brier = brier_sig

    print(f"Heart Calibration Method Selected: {best_cal_method} (Val Brier: {best_val_brier:.4f})")

    # Evaluate on held-out test set
    y_test_proba = calibrated_model.predict_proba(X_test)[:, 1]
    y_test_pred = (y_test_proba >= 0.5).astype(int)

    test_auc = roc_auc_score(y_test, y_test_proba)
    test_acc = accuracy_score(y_test, y_test_pred)
    test_prec = precision_score(y_test, y_test_pred, zero_division=0)
    test_rec = recall_score(y_test, y_test_pred, zero_division=0)
    test_f1 = f1_score(y_test, y_test_pred, zero_division=0)
    test_cm = confusion_matrix(y_test, y_test_pred).tolist()
    test_brier = brier_score_loss(y_test, y_test_proba)
    test_ece = compute_ece(y_test, y_test_proba, n_bins=10)

    prob_true, prob_pred = calibration_curve(y_test, y_test_proba, n_bins=10, strategy="uniform")
    reliability_diagram = [
        {"bin_pred": round(float(p), 4), "observed_rate": round(float(t), 4)}
        for p, t in zip(prob_pred, prob_true)
    ]

    print(f"Heart Test Results -> AUC: {test_auc:.4f}, Acc: {test_acc:.4f}, ECE: {test_ece:.4f}, Brier: {test_brier:.4f}")

    explainer = shap.TreeExplainer(base_model)
    base_val = explainer.expected_value
    if isinstance(base_val, (list, np.ndarray)):
        base_val = float(base_val[1] if len(base_val) > 1 else base_val[0])
    else:
        base_val = float(base_val)

    model_path = os.path.join(MODELS_DIR, "heart_model.joblib")
    explainer_path = os.path.join(MODELS_DIR, "heart_explainer.joblib")
    meta_path = os.path.join(MODELS_DIR, "heart_metadata.json")

    joblib.dump(calibrated_model, model_path)
    joblib.dump(explainer, explainer_path)

    metadata = {
        "disease": "Cardiovascular Disease",
        "data_source": source_info.get("data_source", "real"),
        "dataset_name": source_info.get("dataset_name", "UCI Cleveland Clinic Heart Disease"),
        "source_url": source_info.get("source_url", "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"),
        "row_count": int(source_info.get("row_count", len(df))),
        "date_trained": datetime.now(timezone.utc).isoformat(),
        "feature_cols": feature_cols,
        "calibration_method": best_cal_method,
        "auc_roc": round(float(test_auc), 4),
        "accuracy": round(float(test_acc), 4),
        "precision": round(float(test_prec), 4),
        "recall": round(float(test_rec), 4),
        "f1_score": round(float(test_f1), 4),
        "confusion_matrix": test_cm,
        "brier_score": round(float(test_brier), 4),
        "expected_calibration_error": round(float(test_ece), 4),
        "reliability_diagram": reliability_diagram,
        "base_value": round(base_val, 4),
        "feature_friendly_names": {
            "age": "Patient Age",
            "sex": "Biological Sex",
            "cp": "Chest Pain Type",
            "trestbps": "Resting Blood Pressure",
            "chol": "Serum Cholesterol",
            "fbs": "Fasting Blood Sugar > 120",
            "restecg": "Resting Electrocardiogram (ECG)",
            "thalach": "Maximum Heart Rate Achieved",
            "exang": "Exercise-Induced Angina",
            "oldpeak": "ST Depression (Oldpeak)",
            "slope": "Slope of Peak Exercise ST",
            "ca": "Major Fluoroscopy Vessels Colored"
        }
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Saved calibrated heart model & metadata to {MODELS_DIR}")
    return metadata

if __name__ == "__main__":
    train_diabetes_model()
    train_heart_model()
    print("=" * 60)
    print("All calibrated ML models successfully trained and serialized with SHAP explainers!")
