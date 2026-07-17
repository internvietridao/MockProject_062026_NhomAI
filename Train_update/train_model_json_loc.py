"""
train_model_json_loc.py
=======================

Train Nursing Home Level of Care (LOC) classifier from a 5-core JSON dataset.

Important:
- The JSON dataset is converted from Kaggle Heart Disease Health Indicators.
- This is a proxy healthcare dataset, not an official nursing-home LOC dataset.
- LOC_Level is synthetic and rule-based.
- care_score and LOC_Level are excluded from model input to avoid direct label leakage.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from config_loc_json import JSON_DATA_PATH, MODEL_PATH, RANDOM_STATE, TEST_SIZE
except Exception:
    JSON_DATA_PATH = Path("train/heart_disease_loc_5core.json")
    MODEL_PATH = Path("models/loc_json_best_model.pkl")
    RANDOM_STATE = 42
    TEST_SIZE = 0.2

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except Exception:
    HAS_XGB = False

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except Exception:
    HAS_LGBM = False

warnings.filterwarnings("ignore")


def flatten_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten one 5-core JSON record into tabular features."""
    out: Dict[str, Any] = {}

    cores = record.get("5_cores", {})
    for core_name, features in cores.items():
        if not isinstance(features, dict):
            continue
        for feature_name, value in features.items():
            out[f"{core_name}__{feature_name}"] = value

    # Target only. Do not use care_score as X.
    out["LOC_Level"] = record.get("LOC_Level")
    return out


def load_json_data(path: Path = JSON_DATA_PATH) -> pd.DataFrame:
    """Load and flatten the 5-core JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"JSON dataset not found: {path}\n"
            "Run: python train\\convert_csv_to_5core_json.py first."
        )

    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError("JSON root must be a list of records.")

    df = pd.DataFrame([flatten_record(r) for r in records])

    print("=" * 90)
    print("1. LOAD 5-CORE JSON DATA")
    print("=" * 90)
    print(f"File: {path}")
    print(f"Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print("\nTarget distribution:")
    print(df["LOC_Level"].value_counts().sort_index())

    return df


def clean_flat_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean flattened feature table."""
    df = df.copy()
    df = df.dropna(subset=["LOC_Level"])
    df["LOC_Level"] = df["LOC_Level"].astype(int)

    for col in df.columns:
        if col != "LOC_Level":
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create simple derived features from flattened 5-core columns.

    These are derived from observed proxy features, not from LOC_Level or care_score.
    """
    df = df.copy()

    def col(name: str, default: float = 0.0) -> pd.Series:
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce").fillna(default)
        return pd.Series(default, index=df.index)

    age = col("ADLs_IADLs__Age")
    bmi = col("Clinical_Risk_Assessments__BMI", 25)
    diff_walk = col("ADLs_IADLs__DiffWalk")
    phys = col("ADLs_IADLs__PhysHlth")
    mental = col("Cognitive_Neurological_Status__MentHlth")
    gen = col("Clinical_Risk_Assessments__GenHlth")
    diabetes = col("Clinical_Risk_Assessments__Diabetes")
    stroke = col("Cognitive_Neurological_Status__Stroke")
    heart = col("Clinical_Risk_Assessments__HeartDiseaseorAttack")

    df["Age_x_BMI"] = age * bmi
    df["Age_x_GenHlth"] = age * gen
    df["BMI_Category"] = pd.cut(
        bmi,
        bins=[0, 18.5, 25, 30, 35, 100],
        labels=[0, 1, 2, 3, 4],
        include_lowest=True,
    ).astype(float)
    df["High_Physical_Unhealthy_Days"] = (phys >= 15).astype(int)
    df["High_Mental_Unhealthy_Days"] = (mental >= 15).astype(int)
    df["Mobility_Health_Risk"] = diff_walk + (phys >= 7).astype(int) + (gen >= 4).astype(int)
    df["Clinical_Comorbidity_Count"] = (
        (diabetes > 0).astype(int)
        + (stroke == 1).astype(int)
        + (heart == 1).astype(int)
        + (col("Clinical_Risk_Assessments__HighBP") == 1).astype(int)
        + (col("Clinical_Risk_Assessments__HighChol") == 1).astype(int)
    )
    df["Lifestyle_Risk_Count"] = (
        (col("Mood_Behavioral_Health__Smoker") == 1).astype(int)
        + (col("Mood_Behavioral_Health__HvyAlcoholConsump") == 1).astype(int)
        + (col("ADLs_IADLs__PhysActivity") == 0).astype(int)
    )

    return df


def build_models() -> Dict[str, Any]:
    """Return candidate models."""
    models: Dict[str, Any] = {
        "Logistic Regression": Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(max_iter=1500, class_weight="balanced", random_state=RANDOM_STATE)),
            ]
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=350,
            max_depth=8,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }

    if HAS_XGB:
        models["XGBoost"] = XGBClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

    if HAS_LGBM:
        models["LightGBM"] = LGBMClassifier(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.05,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            verbose=-1,
        )

    return models


def train_and_evaluate(df: pd.DataFrame) -> Any:
    """Train multiple models and select the best by Macro F1."""
    X = df.drop(columns=["LOC_Level"], errors="ignore")
    y = df["LOC_Level"].astype(int)

    # XGBoost expects labels 0,1,2.
    y_xgb = y - 1

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    print("\n" + "=" * 90)
    print("2. TRAIN/TEST SPLIT")
    print("=" * 90)
    print(f"Train samples: {len(X_train):,}")
    print(f"Test samples : {len(X_test):,}")
    print(f"Features     : {X.shape[1]:,}")

    results: List[Dict[str, Any]] = []
    trained: Dict[str, Any] = {}

    print("\n" + "=" * 90)
    print("3. TRAIN MODELS")
    print("=" * 90)

    for name, model in build_models().items():
        print(f"\nTraining: {name}")

        if name == "XGBoost":
            model.fit(X_train, y_train - 1)
            pred = model.predict(X_test) + 1
        else:
            model.fit(X_train, y_train)
            pred = model.predict(X_test)

        acc = accuracy_score(y_test, pred)
        bal = balanced_accuracy_score(y_test, pred)
        macro = f1_score(y_test, pred, average="macro")

        results.append({
            "model": name,
            "accuracy": acc,
            "balanced_accuracy": bal,
            "macro_f1": macro,
        })
        trained[name] = model

        print(f"  Accuracy: {acc:.4f} | Balanced Acc: {bal:.4f} | Macro F1: {macro:.4f}")

    comp = pd.DataFrame(results).sort_values("macro_f1", ascending=False)

    print("\n" + "=" * 90)
    print("4. MODEL COMPARISON")
    print("=" * 90)
    print(comp.to_string(index=False))

    best_name = comp.iloc[0]["model"]
    best_model = trained[best_name]

    if best_name == "XGBoost":
        best_pred = best_model.predict(X_test) + 1
    else:
        best_pred = best_model.predict(X_test)

    print("\n" + "=" * 90)
    print(f"5. FINAL TEST REPORT — {best_name}")
    print("=" * 90)
    print(f"Accuracy          : {accuracy_score(y_test, best_pred):.4f}")
    print(f"Balanced Accuracy : {balanced_accuracy_score(y_test, best_pred):.4f}")
    print(f"Macro F1          : {f1_score(y_test, best_pred, average='macro'):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, best_pred, digits=4))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, best_pred))

    return best_model, best_name, comp


def save_best_model(model: Any, model_name: str, feature_columns: List[str]) -> None:
    """Save model with metadata."""
    path = Path(MODEL_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": model,
        "model_name": model_name,
        "feature_columns": feature_columns,
        "label_note": "LOC_Level is synthetic rule-based label; not official clinical LOC.",
    }
    joblib.dump(artifact, path)
    print("\n" + "=" * 90)
    print("6. SAVE MODEL")
    print("=" * 90)
    print(f"Saved to: {path}")


def main() -> None:
    df = load_json_data()
    df = clean_flat_data(df)
    df = add_engineered_features(df)

    # Safety check: remove leakage columns if they ever appear.
    leakage_cols = [c for c in ["care_score", "LOC_Level"] if c in df.columns and c != "LOC_Level"]
    if leakage_cols:
        df = df.drop(columns=leakage_cols)

    best_model, best_name, comp = train_and_evaluate(df)

    feature_columns = [c for c in df.columns if c != "LOC_Level"]
    save_best_model(best_model, best_name, feature_columns)


if __name__ == "__main__":
    main()
