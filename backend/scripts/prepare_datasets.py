import os
import sys
import argparse
import urllib.request
import json
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

DIABETES_PATH = os.path.join(DATA_DIR, "diabetes_data.csv")
HEART_PATH = os.path.join(DATA_DIR, "heart_disease.csv")
DIABETES_INFO_PATH = os.path.join(DATA_DIR, "diabetes_info.json")
HEART_INFO_PATH = os.path.join(DATA_DIR, "heart_info.json")

DIABETES_FEATURE_COLS = [
    "HighBP", "HighChol", "CholCheck", "BMI", "Smoker", "Stroke",
    "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
    "HvyAlcoholConsump", "GenHlth", "MentHlth", "PhysHlth", "DiffWalk",
    "Sex", "Age"
]
DIABETES_TARGET_COL = "Diabetes_binary"

def prepare_diabetes_dataset(allow_synthetic: bool = False):
    print("=" * 60)
    print("Preparing CDC BRFSS 2015 Diabetes Health Indicators Dataset...")
    df = None
    source_info = {}

    # 1. Preferred method: ucimlrepo package (UCI ID 891)
    try:
        print("[Step 1] Attempting fetch via `ucimlrepo` (UCI Dataset ID: 891)...")
        from ucimlrepo import fetch_ucirepo
        repo = fetch_ucirepo(id=891)
        X = repo.data.features
        y = repo.data.targets
        
        # Ensure target column is present
        target_series = y[DIABETES_TARGET_COL] if DIABETES_TARGET_COL in y.columns else y.iloc[:, 0]
        full_df = X[DIABETES_FEATURE_COLS].copy()
        full_df[DIABETES_TARGET_COL] = target_series.astype(int)
        
        df = full_df.dropna()
        source_info = {
            "data_source": "real",
            "dataset_name": "CDC BRFSS 2015 Diabetes Health Indicators",
            "source_url": "https://archive.ics.uci.edu/dataset/891/cdc+diabetes+health+indicators",
            "row_count": int(len(df)),
            "method": "ucimlrepo"
        }
        print(f"[OK] Successfully downloaded real dataset via ucimlrepo ({len(df)} records).")
    except Exception as e:
        print(f"[Warning] ucimlrepo fetch failed: {e}. Trying plain HTTPS CSV fallback...")

    # 2. Plain HTTPS CSV fallback if ucimlrepo failed
    if df is None:
        csv_fallback_url = "https://archive.ics.uci.edu/static/public/891/data.csv"
        try:
            print(f"[Step 2] Attempting direct HTTPS download from {csv_fallback_url}...")
            raw_path = DIABETES_PATH + ".download"
            req = urllib.request.Request(csv_fallback_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response, open(raw_path, "wb") as out_file:
                out_file.write(response.read())
            
            raw_df = pd.read_csv(raw_path)
            if DIABETES_TARGET_COL in raw_df.columns:
                target_col = DIABETES_TARGET_COL
            elif "Diabetes_012" in raw_df.columns:
                raw_df[DIABETES_TARGET_COL] = (raw_df["Diabetes_012"] > 0).astype(int)
                target_col = DIABETES_TARGET_COL
            else:
                target_col = raw_df.columns[0]
                raw_df[DIABETES_TARGET_COL] = raw_df[target_col].astype(int)

            full_df = raw_df[DIABETES_FEATURE_COLS + [DIABETES_TARGET_COL]].dropna()
            df = full_df
            if os.path.exists(raw_path):
                os.remove(raw_path)

            source_info = {
                "data_source": "real",
                "dataset_name": "CDC BRFSS 2015 Diabetes Health Indicators",
                "source_url": csv_fallback_url,
                "row_count": int(len(df)),
                "method": "https_csv"
            }
            print(f"[OK] Successfully downloaded real dataset via direct HTTPS ({len(df)} records).")
        except Exception as e:
            print(f"[Warning] Direct HTTPS download failed: {e}")

    # 3. Synthetic fallback only if explicit flag --allow-synthetic is provided
    if df is None:
        if not allow_synthetic:
            err_msg = (
                "FATAL: Network unavailable or UCI repository unreachable, and real CDC diabetes dataset "
                "could not be downloaded. Per ground rules, silent fallback to synthetic data is forbidden. "
                "To explicitly enable the synthetic demo generator, re-run with: python scripts/prepare_datasets.py --allow-synthetic"
            )
            print(err_msg, file=sys.stderr)
            raise RuntimeError(err_msg)

        print("[Notice] Using explicit synthetic generator fallback (--allow-synthetic requested)...")
        np.random.seed(101)
        n = 2500
        age = np.random.normal(52, 14, n).clip(20, 85).astype(int)
        sex = np.random.choice([0, 1], n, p=[0.48, 0.52])
        bmi = np.random.normal(28.5, 6.2, n).clip(17.0, 55.0).round(1)
        high_bp = (np.random.rand(n) < (0.20 + 0.008 * age + 0.015 * (bmi - 25).clip(0))).astype(int)
        high_chol = (np.random.rand(n) < (0.22 + 0.007 * age + 0.01 * (bmi - 25).clip(0))).astype(int)
        chol_check = np.random.choice([0, 1], n, p=[0.05, 0.95])
        smoker = np.random.choice([0, 1], n, p=[0.55, 0.45])
        stroke = (np.random.rand(n) < (0.01 + 0.002 * (age > 60) + 0.03 * high_bp)).astype(int)
        heart_disease = (np.random.rand(n) < (0.04 + 0.003 * (age > 50) + 0.05 * high_bp + 0.04 * smoker)).astype(int)
        phys_activity = (np.random.rand(n) < (0.80 - 0.005 * age - 0.01 * (bmi - 25).clip(0))).astype(int)
        fruits = np.random.choice([0, 1], n, p=[0.38, 0.62])
        veggies = np.random.choice([0, 1], n, p=[0.22, 0.78])
        hvy_alcohol = np.random.choice([0, 1], n, p=[0.92, 0.08])
        gen_hlth = (1 + (bmi > 30) + high_bp + (1 - phys_activity) + np.random.choice([0, 1], n, p=[0.7, 0.3])).clip(1, 5)
        ment_hlth = np.random.choice([0, 2, 5, 10, 20], n, p=[0.55, 0.20, 0.12, 0.08, 0.05])
        phys_hlth = np.random.choice([0, 1, 4, 10, 25], n, p=[0.50, 0.22, 0.15, 0.08, 0.05])
        diff_walk = (np.random.rand(n) < (0.05 + 0.005 * (age > 60) + 0.02 * (bmi > 35))).astype(int)

        logits = (
            -4.2
            + 0.04 * (age - 45)
            + 0.09 * (bmi - 25)
            + 0.95 * high_bp
            + 0.75 * high_chol
            + 0.40 * smoker
            + 0.60 * heart_disease
            - 0.50 * phys_activity
            + 0.45 * (gen_hlth - 2)
            + 0.50 * diff_walk
        )
        prob = 1.0 / (1.0 + np.exp(-logits))
        target = (np.random.rand(n) < prob).astype(int)

        df = pd.DataFrame({
            "HighBP": high_bp, "HighChol": high_chol, "CholCheck": chol_check,
            "BMI": bmi, "Smoker": smoker, "Stroke": stroke,
            "HeartDiseaseorAttack": heart_disease, "PhysActivity": phys_activity,
            "Fruits": fruits, "Veggies": veggies, "HvyAlcoholConsump": hvy_alcohol,
            "GenHlth": gen_hlth, "MentHlth": ment_hlth, "PhysHlth": phys_hlth,
            "DiffWalk": diff_walk, "Sex": sex, "Age": age,
            "Diabetes_binary": target
        })
        source_info = {
            "data_source": "synthetic_demo",
            "dataset_name": "Synthetic Diabetes Demo Dataset (np.random generated)",
            "source_url": "synthetic://local_generator",
            "row_count": int(len(df)),
            "method": "synthetic_generator"
        }

    # Save CSV and source info
    df.to_csv(DIABETES_PATH, index=False)
    with open(DIABETES_INFO_PATH, "w") as f:
        json.dump(source_info, f, indent=2)
    print(f"[OK] Saved diabetes dataset ({len(df)} rows, source: {source_info['data_source']}) to {DIABETES_PATH}")
    return source_info

def prepare_heart_disease_dataset(allow_synthetic: bool = False):
    print("=" * 60)
    print("Preparing UCI Cleveland Heart Disease Dataset...")
    uci_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
    columns = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", 
        "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"
    ]
    df = None
    source_info = {}

    try:
        print(f"Downloading from UCI Cleveland repository: {uci_url}...")
        req = urllib.request.Request(uci_url, headers={"User-Agent": "Mozilla/5.0"})
        raw_path = HEART_PATH + ".raw"
        with urllib.request.urlopen(req, timeout=20) as resp, open(raw_path, "wb") as f_out:
            f_out.write(resp.read())

        raw_df = pd.read_csv(raw_path, names=columns, na_values="?")
        raw_df = raw_df.dropna()
        # Binary target: 0 = healthy, 1 = disease present
        raw_df["target"] = (raw_df["target"] > 0).astype(int)
        df = raw_df
        if os.path.exists(raw_path):
            os.remove(raw_path)

        source_info = {
            "data_source": "real",
            "dataset_name": "UCI Cleveland Clinic Heart Disease",
            "source_url": uci_url,
            "row_count": int(len(df)),
            "method": "direct_download"
        }
        print(f"[OK] UCI Cleveland heart disease dataset successfully fetched ({len(df)} records).")
    except Exception as e:
        print(f"[Warning] Direct heart dataset download failed: {e}")

    if df is None:
        if not allow_synthetic:
            err_msg = (
                "FATAL: UCI Heart Disease repository unreachable, and real Cleveland dataset could not be fetched. "
                "To explicitly enable synthetic fallback, run with: python scripts/prepare_datasets.py --allow-synthetic"
            )
            print(err_msg, file=sys.stderr)
            raise RuntimeError(err_msg)

        print("[Notice] Using explicit synthetic heart dataset generator...")
        np.random.seed(42)
        n = 1200
        age = np.random.normal(54, 10, n).clip(28, 85).astype(int)
        sex = np.random.choice([0, 1], n, p=[0.35, 0.65])
        cp = np.random.choice([0, 1, 2, 3], n, p=[0.25, 0.20, 0.35, 0.20])
        trestbps = np.random.normal(132, 18, n).clip(90, 200).astype(int)
        chol = np.random.normal(245, 45, n).clip(120, 480).astype(int)
        fbs = (np.random.rand(n) < (0.15 + 0.1 * (age > 55))).astype(int)
        restecg = np.random.choice([0, 1, 2], n, p=[0.5, 0.45, 0.05])
        thalach = (220 - age - np.random.normal(20, 15, n)).clip(70, 205).astype(int)
        exang = np.random.choice([0, 1], n, p=[0.68, 0.32])
        oldpeak = np.abs(np.random.exponential(1.1, n)).clip(0.0, 6.2).round(1)
        slope = np.random.choice([0, 1, 2], n, p=[0.15, 0.45, 0.40])
        ca = np.random.choice([0, 1, 2, 3], n, p=[0.58, 0.22, 0.14, 0.06])
        thal = np.random.choice([3, 6, 7], n, p=[0.55, 0.10, 0.35])

        logits = (
            -5.0
            + 0.04 * (age - 50)
            + 0.6 * sex
            + 0.5 * (cp == 0)
            + 0.02 * (trestbps - 120)
            + 0.008 * (chol - 200)
            + 0.5 * fbs
            - 0.03 * (thalach - 130)
            + 0.9 * exang
            + 0.7 * oldpeak
            + 0.6 * (ca > 0)
        )
        prob = 1.0 / (1.0 + np.exp(-logits))
        target = (np.random.rand(n) < prob).astype(int)

        df = pd.DataFrame({
            "age": age, "sex": sex, "cp": cp, "trestbps": trestbps, "chol": chol,
            "fbs": fbs, "restecg": restecg, "thalach": thalach, "exang": exang,
            "oldpeak": oldpeak, "slope": slope, "ca": ca, "thal": thal, "target": target
        })
        source_info = {
            "data_source": "synthetic_demo",
            "dataset_name": "Synthetic Heart Disease Benchmark Dataset",
            "source_url": "synthetic://local_generator",
            "row_count": int(len(df)),
            "method": "synthetic_generator"
        }

    df.to_csv(HEART_PATH, index=False)
    with open(HEART_INFO_PATH, "w") as f:
        json.dump(source_info, f, indent=2)
    print(f"[OK] Saved heart disease dataset ({len(df)} rows, source: {source_info['data_source']}) to {HEART_PATH}")
    return source_info

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and prepare real clinical benchmark datasets.")
    parser.add_argument("--allow-synthetic", action="store_true", help="Explicit fallback to synthetic data if network/repository is unavailable.")
    args = parser.parse_args()

    prepare_diabetes_dataset(allow_synthetic=args.allow_synthetic)
    prepare_heart_disease_dataset(allow_synthetic=args.allow_synthetic)
    print("=" * 60)
    print("Dataset preparation complete.")
