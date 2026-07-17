"""
convert_csv_to_5core_json.py
================================

Convert Kaggle Heart Disease Health Indicators CSV into a 5-core JSON dataset
for an academic Nursing Home Level of Care (LOC) classification demo.

Important:
- This is NOT an official nursing-home LOC dataset.
- LOC_Level is a synthetic rule-based label created for academic demonstration.
- care_score is saved for audit/explanation, but must NOT be used as a model input.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd

try:
    from config_loc_json import (
        RAW_CSV_PATH,
        JSON_DATA_PATH,
        MIN_AGE_GROUP,
        STRICT_FILTER,
        STRICT_MIN_AGE_GROUP,
    )
except Exception:
    RAW_CSV_PATH = Path("heart_disease_health_indicators_BRFSS2015.csv")
    JSON_DATA_PATH = Path("train/heart_disease_loc_5core.json")
    MIN_AGE_GROUP = 7
    STRICT_FILTER = False
    STRICT_MIN_AGE_GROUP = 9


EXPECTED_COLUMNS = [
    "HeartDiseaseorAttack", "HighBP", "HighChol", "CholCheck", "BMI",
    "Smoker", "Stroke", "Diabetes", "PhysActivity", "Fruits", "Veggies",
    "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "GenHlth",
    "MentHlth", "PhysHlth", "DiffWalk", "Sex", "Age", "Education", "Income",
]


# ---------------------------------------------------------------------------
# BALANCE OUTPUT JSON
# ---------------------------------------------------------------------------
# Mục tiêu: giữ Level 1 nguyên vẹn, giảm Level 2 và Level 3 xuống khoảng 5,000 mẫu mỗi level.
# Lưu ý: Level 1 hiện chỉ có khoảng 459 mẫu nên không thể tăng lên nếu không oversampling.
BALANCE_LEVEL_OUTPUT = True
MAX_SAMPLES_PER_LEVEL = {
    1: None,   # None = giữ toàn bộ Level 1
    2: 5000,
    3: 5000,
}
BALANCE_RANDOM_STATE = 42


def balance_records_by_level(records):
    """Giảm số mẫu theo từng LOC_Level để tránh Level 2/3 quá nhiều."""
    if not BALANCE_LEVEL_OUTPUT:
        return records

    df_records = pd.DataFrame(records)

    balanced_parts = []
    for level in sorted(df_records["LOC_Level"].unique()):
        part = df_records[df_records["LOC_Level"] == level]
        max_n = MAX_SAMPLES_PER_LEVEL.get(int(level), None)

        if max_n is not None and len(part) > max_n:
            part = part.sample(n=max_n, random_state=BALANCE_RANDOM_STATE)

        balanced_parts.append(part)

    balanced_df = pd.concat(balanced_parts, axis=0)
    balanced_df = balanced_df.sample(frac=1, random_state=BALANCE_RANDOM_STATE).reset_index(drop=True)

    return balanced_df.to_dict(orient="records")



def to_number(value: Any) -> float:
    """Convert values to Python float for JSON serialization."""
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except Exception:
        return 0.0


def compute_care_score(row: pd.Series) -> int:
    """
    Synthetic care_score based on proxy variables.

    Stronger weight:
    - functional limitation / mobility proxy: DiffWalk
    - poor general health: GenHlth
    - many physically unhealthy days: PhysHlth
    - major clinical risks: Stroke, Diabetes, HeartDiseaseorAttack

    This is a rule-based academic approximation, not an official clinical LOC rule.
    """
    s = 0

    # General / age proxy. BRFSS Age is categorical.
    age = row.get("Age", 0)
    if age >= 10:
        s += 2
    elif age >= 8:
        s += 1

    # ADL / functional ability proxies
    if row.get("DiffWalk", 0) == 1:
        s += 3
    if row.get("PhysActivity", 1) == 0:
        s += 1

    # Overall health status
    gen = row.get("GenHlth", 1)
    if gen >= 4:
        s += 3
    elif gen == 3:
        s += 1

    # Physical and mental health days
    phys = row.get("PhysHlth", 0)
    if phys >= 15:
        s += 2
    elif phys >= 7:
        s += 1

    ment = row.get("MentHlth", 0)
    if ment >= 15:
        s += 1

    # Clinical risks
    if row.get("HighBP", 0) == 1:
        s += 1
    if row.get("HighChol", 0) == 1:
        s += 1
    if row.get("Diabetes", 0) > 0:
        s += 2
    if row.get("Stroke", 0) == 1:
        s += 2
    if row.get("HeartDiseaseorAttack", 0) == 1:
        s += 2

    # Nutrition / BMI proxy
    bmi = row.get("BMI", 25)
    if bmi >= 35:
        s += 1
    if bmi < 18.5:
        s += 1

    # Behavioral/lifestyle proxies
    if row.get("Smoker", 0) == 1:
        s += 1
    if row.get("HvyAlcoholConsump", 0) == 1:
        s += 1

    # Access-to-care / social proxy
    if row.get("NoDocbcCost", 0) == 1:
        s += 1

    return int(s)


def score_to_level(score: int) -> int:
    """Convert care_score into 3 synthetic LOC levels."""
    if score <= 3:
        return 1
    if score <= 8:
        return 2
    return 3


def row_to_5core_record(row: pd.Series, source_id: int) -> Dict[str, Any]:
    """Build one structured 5-core JSON record."""
    score = compute_care_score(row)
    level = score_to_level(score)

    return {
        "source_id": int(source_id),
        "data_source": "Kaggle Heart Disease Health Indicators BRFSS2015",
        "label_type": "synthetic_rule_based_loc",
        "5_cores": {
            "ADLs_IADLs": {
                "Age": to_number(row.get("Age", 0)),
                "DiffWalk": to_number(row.get("DiffWalk", 0)),
                "PhysActivity": to_number(row.get("PhysActivity", 0)),
                "PhysHlth": to_number(row.get("PhysHlth", 0)),
            },
            "Cognitive_Neurological_Status": {
                "Stroke": to_number(row.get("Stroke", 0)),
                "MentHlth": to_number(row.get("MentHlth", 0)),
            },
            "Clinical_Risk_Assessments": {
                "HeartDiseaseorAttack": to_number(row.get("HeartDiseaseorAttack", 0)),
                "HighBP": to_number(row.get("HighBP", 0)),
                "HighChol": to_number(row.get("HighChol", 0)),
                "CholCheck": to_number(row.get("CholCheck", 0)),
                "Diabetes": to_number(row.get("Diabetes", 0)),
                "BMI": to_number(row.get("BMI", 0)),
                "GenHlth": to_number(row.get("GenHlth", 0)),
                "PhysHlth": to_number(row.get("PhysHlth", 0)),
                "AnyHealthcare": to_number(row.get("AnyHealthcare", 0)),
            },
            "Mood_Behavioral_Health": {
                "MentHlth": to_number(row.get("MentHlth", 0)),
                "Smoker": to_number(row.get("Smoker", 0)),
                "HvyAlcoholConsump": to_number(row.get("HvyAlcoholConsump", 0)),
                "Fruits": to_number(row.get("Fruits", 0)),
                "Veggies": to_number(row.get("Veggies", 0)),
            },
            "Financial_Legal_General_Status": {
                "Age": to_number(row.get("Age", 0)),
                "Sex": to_number(row.get("Sex", 0)),
                "Education": to_number(row.get("Education", 0)),
                "Income": to_number(row.get("Income", 0)),
                "NoDocbcCost": to_number(row.get("NoDocbcCost", 0)),
                "AnyHealthcare": to_number(row.get("AnyHealthcare", 0)),
            },
        },
        "care_score": score,
        "LOC_Level": level,
    }


def describe_distribution(df: pd.DataFrame, title: str) -> None:
    print("\n" + "=" * 90)
    print(f"EDA REPORT — {title}")
    print("=" * 90)
    print(f"Rows: {len(df):,}")

    for col in [
        "Age",
        "GenHlth",
        "PhysHlth",
        "MentHlth",
        "DiffWalk",
        "PhysActivity",
        "Stroke",
        "Diabetes",
        "HeartDiseaseorAttack",
        "HighBP",
        "HighChol",
    ]:
        if col in df.columns:
            print(f"\n{col} distribution:")
            print(df[col].value_counts().sort_index().to_string())


def apply_strict_filter(df: pd.DataFrame) -> pd.DataFrame:
    if not STRICT_FILTER:
        return df

    print("\nApplying strict nursing-home proxy filter...")
    age_filtered = df[df["Age"] >= STRICT_MIN_AGE_GROUP]
    functional = (age_filtered["DiffWalk"] == 1) | (age_filtered["PhysActivity"] == 0)
    clinical = (
        (age_filtered["GenHlth"] >= 3)
        | (age_filtered["PhysHlth"] >= 7)
        | (age_filtered["MentHlth"] >= 7)
        | (age_filtered["Stroke"] == 1)
        | (age_filtered["Diabetes"] > 0)
        | (age_filtered["HeartDiseaseorAttack"] == 1)
        | (age_filtered["HighBP"] == 1)
        | (age_filtered["HighChol"] == 1)
    )
    filtered = age_filtered[functional & clinical].reset_index(drop=True)
    print(
        f"Strict filter kept {len(filtered):,} / {len(df):,} rows "
        f"after age >= {STRICT_MIN_AGE_GROUP} and proxy risk criteria."
    )
    return filtered


def main() -> None:
    csv_path = Path(RAW_CSV_PATH)
    json_path = Path(JSON_DATA_PATH)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    df = df[EXPECTED_COLUMNS].copy()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    describe_distribution(df, "Raw CSV before filtering")

    # Keep older-adult records to better match nursing-home context.
    df = df[df["Age"] >= MIN_AGE_GROUP].reset_index(drop=True)

    df = apply_strict_filter(df)
    describe_distribution(df, "After applied strict nursing-home-like filter")

    # Clip extreme values but do not drop rows.
    df["BMI"] = df["BMI"].clip(lower=12, upper=60)
    df["MentHlth"] = df["MentHlth"].clip(lower=0, upper=30)
    df["PhysHlth"] = df["PhysHlth"].clip(lower=0, upper=30)

    records = [row_to_5core_record(row, i) for i, row in df.iterrows()]

    print("\nBefore balancing LOC_Level distribution:")
    print(pd.Series([r["LOC_Level"] for r in records]).value_counts().sort_index())

    records = balance_records_by_level(records)

    print("\nAfter balancing LOC_Level distribution:")
    print(pd.Series([r["LOC_Level"] for r in records]).value_counts().sort_index())

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    levels = pd.Series([r["LOC_Level"] for r in records]).value_counts().sort_index()

    print("=" * 90)
    print("CSV -> 5-CORE JSON CONVERSION DONE")
    print("=" * 90)
    print(f"Input CSV : {csv_path}")
    print(f"Output JSON: {json_path}")
    print(f"Rows kept : {len(records):,}")
    print("\nLOC_Level distribution:")
    print(levels)


if __name__ == "__main__":
    main()
